# 5. Hệ thống giám sát

Chương này trình bày thiết kế và cài đặt hệ thống giám sát thời gian thực — thành phần thu nhận chỉ số từ bộ mô phỏng, tổng hợp theo cửa sổ trượt, phát hiện bất thường và phát sinh cảnh báo.

## 5.1. Kiến trúc hệ thống giám sát

Hệ thống giám sát gồm bốn khối chức năng nối tiếp nhau:

```
        Sự kiện từ bộ mô phỏng
                  │
                  ▼
        ┌──────────────────────┐
        │  Bộ tổng hợp cửa sổ   │
        │     (Aggregator)      │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  Bộ đệm chuỗi thời    │
        │   gian (Buffer)       │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  Bộ phát hiện bất     │
        │  thường (Detector)    │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  Bộ quản lý cảnh báo  │
        │     (Alert Mgr)       │
        └──────────┬───────────┘
                   │
                   ▼
          Dashboard / API
```

- **Bộ tổng hợp:** gom các sự kiện thô (phát thành công, xung đột…) trong mỗi cửa sổ 100 ms thành một mẫu chỉ số.
- **Bộ đệm chuỗi thời gian:** lưu giữ các mẫu gần nhất theo cửa sổ trượt.
- **Bộ phát hiện bất thường:** kiểm tra mỗi mẫu mới so với ngưỡng và mô hình học máy.
- **Bộ quản lý cảnh báo:** phát sinh, lọc trùng và đẩy cảnh báo ra giao diện.

## 5.2. Thu thập và tổng hợp chỉ số

### 5.2.1. Tổng hợp theo cửa sổ

Bộ tổng hợp tích lũy các sự kiện trong mỗi khoảng 100 ms rồi tính ra một mẫu chỉ số cho khoảng đó:

```python
class WindowAggregator:
    def __init__(self, window=0.1):     # cửa sổ 100 ms
        self.window = window
        self.reset()

    def reset(self):
        self.bytes_ok = 0
        self.n_collision = 0
        self.n_total = 0
        self.latencies = []

    def add_event(self, event):
        if event.type == 'success':
            self.bytes_ok += event.size
            self.latencies.append(event.latency)
            self.n_total += 1
        elif event.type == 'collision':
            self.n_collision += 1
            self.n_total += 1

    def flush(self, t):
        sample = {
            't': t,
            'throughput_mbps': self.bytes_ok * 8 / self.window / 1e6,
            'collision_rate': self.n_collision / max(self.n_total, 1),
            'latency_mean_ms': np.mean(self.latencies)*1000 if self.latencies else 0,
        }
        self.reset()
        return sample
```

### 5.2.2. Bộ đệm chuỗi thời gian (cửa sổ trượt)

Bộ đệm lưu các mẫu gần nhất bằng cấu trúc hàng đợi hai đầu có giới hạn độ dài, tự động loại bỏ mẫu cũ nhất khi đầy:

```python
from collections import deque

class TimeSeriesBuffer:
    def __init__(self, seconds=10, rate=10):    # 10 giây, 10 mẫu/giây
        self.buffer = deque(maxlen=seconds * rate)

    def add(self, sample):
        self.buffer.append(sample)

    def get_window(self, n):
        return list(self.buffer)[-n:]
```

Cửa sổ trượt này vừa cung cấp dữ liệu cho việc phát hiện bất thường, vừa là nguồn đầu vào cho mô hình AI dự đoán (Chương 6).

## 5.3. Phát hiện bất thường

Hệ thống kết hợp hai phương pháp phát hiện bất thường bổ trợ cho nhau.

### 5.3.1. Phương pháp dựa trên ngưỡng

Phương pháp đơn giản và dễ giải thích: mỗi chỉ số được so với một ngưỡng định trước, vượt ngưỡng thì coi là bất thường.

```python
THRESHOLDS = {
    'latency_p99_ms':       {'max': 100},
    'collision_rate':       {'max': 0.30},
    'channel_utilization':  {'max': 0.95},
}

def threshold_check(sample):
    alerts = []
    for metric, rule in THRESHOLDS.items():
        if 'max' in rule and sample[metric] > rule['max']:
            alerts.append(f'{metric} vượt ngưỡng: {sample[metric]:.2f}')
    return alerts
```

### 5.3.2. Phương pháp học máy (Isolation Forest)

Để phát hiện các bất thường phức tạp mà ngưỡng đơn giản bỏ sót, hệ thống dùng thêm mô hình Isolation Forest — một thuật toán học không giám sát phát hiện điểm dị biệt. Mô hình được huấn luyện trên dữ liệu trạng thái bình thường của mạng, sau đó đánh dấu các mẫu lệch khỏi phân bố bình thường.

```python
from sklearn.ensemble import IsolationForest

class MLDetector:
    def __init__(self, contamination=0.1):
        self.model = IsolationForest(contamination=contamination,
                                     random_state=42)

    def fit(self, normal_samples):
        self.model.fit(normal_samples)

    def is_anomaly(self, sample_vector):
        return self.model.predict([sample_vector])[0] == -1
```

## 5.4. Quản lý cảnh báo

Bộ quản lý cảnh báo nhận kết quả từ các bộ phát hiện, phân loại mức độ nghiêm trọng và tránh phát cảnh báo trùng lặp liên tục bằng cơ chế thời gian chờ (cooldown):

```python
class AlertManager:
    def __init__(self, cooldown=5.0):
        self.cooldown = cooldown
        self.last_time = {}

    def raise_alert(self, level, message, t):
        key = (level, message)
        if t - self.last_time.get(key, -1e9) < self.cooldown:
            return                      # vẫn trong thời gian chờ → bỏ qua
        self.last_time[key] = t
        self.publish(level, message, t)  # đẩy ra dashboard

    def publish(self, level, message, t):
        ...   # gửi qua WebSocket tới giao diện
```

Cảnh báo được chia làm các mức như `WARNING` (cần chú ý) và `CRITICAL` (nghiêm trọng, sắp quá tải), giúp người theo dõi ưu tiên xử lý.

## 5.5. Truyền dữ liệu thời gian thực

Để dashboard hiển thị được theo thời gian thực, hệ thống giám sát đẩy dữ liệu qua giao thức WebSocket với tần suất 10 lần/giây. Một máy chủ FastAPI đảm nhiệm việc này:

```python
@app.websocket('/ws/metrics')
async def stream(ws):
    await ws.accept()
    while simulator.is_running():
        sample = monitor.latest_sample()
        await ws.send_json(sample)
        await asyncio.sleep(0.1)        # 10 Hz
```

Nhờ kiến trúc này, các chỉ số mạng, kết quả phát hiện bất thường và cảnh báo được truyền liên tục tới giao diện, tạo nên trải nghiệm giám sát thời gian thực. Dữ liệu chuỗi thời gian từ hệ thống giám sát đồng thời là đầu vào cho mô hình AI dự đoán, được trình bày ở chương tiếp theo.
