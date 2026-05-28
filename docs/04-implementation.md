# 4. Triển khai mô phỏng

Chương này trình bày việc cài đặt bộ mô phỏng: tổ chức mã nguồn, engine sự kiện rời rạc, cài đặt cơ chế CSMA/CA và OFDMA, cách đo lường các chỉ số, và kết quả kiểm chứng với mô hình Bianchi.

## 4.1. Tổ chức mã nguồn

Mã nguồn của project được tổ chức thành các thư mục theo chức năng:

```
CSMA-OFDMA-AI-SIMULATOR/
├── simulator/        # Bộ mô phỏng (DES engine, CSMA/CA, OFDMA)
├── monitoring/       # Hệ thống giám sát thời gian thực
├── ai/               # Mô hình AI và huấn luyện
├── analysis/         # Phân tích kết quả, đối chiếu Bianchi
├── frontend/         # Giao diện dashboard
├── scripts/          # Script chạy mô phỏng, sinh dữ liệu, huấn luyện
├── notebooks/        # Jupyter notebook thử nghiệm
├── tests/            # Kiểm thử đơn vị
├── results/          # Dữ liệu và kết quả đầu ra
└── docs/             # Tài liệu
```

Riêng thư mục `simulator/` — phần lõi — được chia nhỏ thành: `core/` (engine sự kiện, đồng hồ mô phỏng), `mac/` (cài đặt CSMA/CA và OFDMA), `entities/` (AP, STA, kênh, gói tin), và `metrics/` (thu thập chỉ số).

## 4.2. Engine mô phỏng sự kiện rời rạc

Trái tim của bộ mô phỏng là bộ điều phối sự kiện, sử dụng một hàng đợi ưu tiên để luôn xử lý sự kiện có thời điểm sớm nhất. Cấu trúc cơ bản:

```python
import heapq

class EventScheduler:
    def __init__(self):
        self.queue = []        # hàng đợi ưu tiên (min-heap theo thời gian)
        self.now = 0.0         # đồng hồ mô phỏng

    def schedule(self, time, event):
        heapq.heappush(self.queue, (time, event))

    def run(self, until):
        while self.queue and self.now < until:
            time, event = heapq.heappop(self.queue)
            self.now = time
            new_events = event.execute()       # xử lý sự kiện
            for t, e in new_events:            # đưa sự kiện mới vào hàng đợi
                self.schedule(t, e)
```

Cách tiếp cận này cho phép bộ mô phỏng "nhảy" trực tiếp đến thời điểm của sự kiện kế tiếp thay vì duyệt từng bước thời gian nhỏ, giúp mô phỏng 30 giây hoạt động của mạng chỉ trong vài giây thực thi.

## 4.3. Cài đặt cơ chế CSMA/CA

### 4.3.1. Máy trạng thái

Mỗi STA được mô hình hóa như một máy trạng thái (state machine) với các trạng thái: `IDLE` (rảnh), `SENSING` (đang lắng nghe kênh), `BACKOFF` (đang đếm lùi), `TRANSMIT` (đang phát) và `WAIT_ACK` (chờ xác nhận). Quá trình chuyển trạng thái tuân theo đúng quy trình DCF đã mô tả ở mục 2.2.2.

```
        ┌──────────┐
        │   IDLE   │
        └────┬─────┘
             │ có gói cần gửi
             ▼
        ┌──────────┐
        │ SENSING  │◄─────┐
        └────┬─────┘      │ kênh bận
             │ rảnh DIFS  │
             ▼            │
        ┌──────────┐──────┘
        │ BACKOFF  │
        └────┬─────┘
             │ counter = 0
             ▼
        ┌──────────┐
        │ TRANSMIT │
        └────┬─────┘
             │
             ▼
        ┌──────────┐  timeout (tăng CW)
        │ WAIT_ACK │──────────────► BACKOFF
        └────┬─────┘
             │ nhận ACK
             ▼
        ┌──────────┐
        │   IDLE   │
        └──────────┘
```

### 4.3.2. Thuật toán backoff

Cốt lõi của CSMA/CA là cơ chế backoff nhị phân. Khi một STA cần phát, nó chọn ngẫu nhiên giá trị backoff và đếm lùi; khi thất bại thì nhân đôi cửa sổ tranh chấp:

```python
class CSMA_CA:
    def __init__(self):
        self.cw = CW_MIN
        self.stage = 0

    def choose_backoff(self):
        return random.randint(0, self.cw)

    def on_success(self):
        self.cw = CW_MIN          # phát thành công → reset
        self.stage = 0

    def on_failure(self):
        self.stage = min(self.stage + 1, MAX_STAGE)
        self.cw = min(2 * self.cw + 1, CW_MAX)   # nhân đôi cửa sổ
```

### 4.3.3. Phát hiện xung đột

Trong môi trường mô phỏng, xung đột được phát hiện bằng cách kiểm tra: nếu trong cùng một khoảng thời gian có từ hai STA trở lên ở trạng thái `TRANSMIT`, tất cả các lượt phát đó đều thất bại.

```python
def check_collision(transmitting_stations):
    if len(transmitting_stations) > 1:
        for sta in transmitting_stations:
            sta.on_failure()       # tất cả đều xung đột
        return True
    return False
```

## 4.4. Cài đặt cơ chế OFDMA

### 4.4.1. Cấp phát Resource Unit

Số lượng và kích thước RU được quyết định dựa trên số STA cần phục vụ. Một kênh 20 MHz (242 tone) được chia thành các RU như sau:

```python
class RUAllocator:
    def allocate(self, n_active):
        if n_active <= 1:   return [242]            # 1 RU lớn
        elif n_active <= 2: return [106, 106]       # 2 RU
        elif n_active <= 4: return [52, 52, 52, 52] # 4 RU
        else:               return [26] * 9         # 9 RU nhỏ
```

### 4.4.2. Trigger Frame và truyền song song

Sau khi AP giành kênh bằng CSMA/CA, nó gửi Trigger Frame và các STA được chọn cùng phát song song. Vì các RU không chồng lấn về tần số, các lượt phát song song này **không gây xung đột với nhau**:

```python
def ofdma_cycle(ap, stations):
    # 1. AP giành kênh bằng CSMA/CA
    ap.contend_for_channel()

    # 2. Chọn STA và cấp RU theo Round-Robin
    selected = ap.scheduler.select(stations, n_ru)
    rus = ap.ru_allocator.allocate(len(selected))

    # 3. Gửi Trigger Frame (tốn thời gian T_TF)
    ap.send_trigger_frame(selected)

    # 4. Các STA phát song song trên RU của mình
    end_time = max(sta.transmit_on_ru(ru)
                   for sta, ru in zip(selected, rus))

    # 5. AP gửi Block ACK xác nhận
    ap.send_block_ack(selected)
    return end_time
```

### 4.4.3. Lập lịch Round-Robin

Bộ lập lịch chọn các STA có dữ liệu chờ gửi theo nguyên tắc luân phiên, đảm bảo mọi STA đều có cơ hội được phục vụ, qua đó duy trì tính công bằng:

```python
class RoundRobinScheduler:
    def __init__(self):
        self.last = 0

    def select(self, stations, n_slots):
        ready = [s for s in stations if s.has_data()]
        chosen = []
        for i in range(min(n_slots, len(ready))):
            chosen.append(ready[(self.last + i) % len(ready)])
        self.last += len(chosen)
        return chosen
```

## 4.5. Đo lường các chỉ số

Lớp `MetricsCollector` ghi nhận các sự kiện trong suốt quá trình mô phỏng và tính năm chỉ số theo công thức ở mục 2.4. Việc đo được thực hiện ở hai cấp độ: tổng hợp toàn cục cho cả lần chạy, và theo cửa sổ 100 ms cho chuỗi thời gian.

```python
class MetricsCollector:
    def __init__(self):
        self.bits_success = 0
        self.n_collisions = 0
        self.n_success = 0
        self.latencies = []
        self.per_sta_bits = defaultdict(int)

    def on_success(self, packet, sta_id):
        self.bits_success += packet.size * 8
        self.n_success += 1
        self.latencies.append(packet.ack_time - packet.created_time)
        self.per_sta_bits[sta_id] += packet.size * 8

    def on_collision(self):
        self.n_collisions += 1

    def summary(self, sim_time):
        x = list(self.per_sta_bits.values())
        return {
            'throughput_mbps': self.bits_success / sim_time / 1e6,
            'latency_mean_ms': np.mean(self.latencies) * 1000,
            'latency_p99_ms':  np.percentile(self.latencies, 99) * 1000,
            'collision_rate':  self.n_collisions / (self.n_collisions + self.n_success),
            'fairness_index':  sum(x)**2 / (len(x) * sum(xi**2 for xi in x)),
            'channel_utilization': self.busy_success_time / sim_time,
        }
```

## 4.6. Kiểm chứng với mô hình Bianchi

### 4.6.1. Quy trình kiểm chứng

Để kiểm chứng tính đúng đắn, bộ mô phỏng được cấu hình ở chế độ tương đương với giả định của Bianchi (chỉ CSMA/CA, lưu lượng bão hòa, không lỗi PHY), sau đó so sánh thông lượng đo được với thông lượng tính theo công thức Bianchi (mục 3.2.5).

Mô hình Bianchi được cài đặt trong thư mục `analysis/` bằng cách giải hệ phương trình $\tau$–$p$:

```python
from scipy.optimize import fsolve

def bianchi(n, W=15, m=6):
    def eqs(v):
        tau, p = v
        e1 = tau - 2*(1-2*p) / ((1-2*p)*(W+1) + p*W*(1-(2*p)**m))
        e2 = p - (1 - (1-tau)**(n-1))
        return [e1, e2]
    tau, p = fsolve(eqs, [0.1, 0.1])
    return tau, p
```

### 4.6.2. Cấu hình thử nghiệm

Quá trình kiểm chứng được thực hiện với các tham số chuẩn 802.11: tốc độ dữ liệu 54 Mbps, payload 1500 byte, CWmin = 15, CWmax = 1023, SlotTime = 9 μs, SIFS = 16 μs, DIFS = 34 μs. Số STA được thay đổi lần lượt $n \in \{5, 10, 20, 30, 50, 75, 100\}$, mỗi giá trị chạy nhiều lần với hạt giống ngẫu nhiên khác nhau để tính khoảng tin cậy.

### 4.6.3. Tiêu chí đạt

Bộ mô phỏng được coi là đúng nếu sai số tương đối giữa thông lượng đo được và thông lượng lý thuyết Bianchi nhỏ hơn 3% trên toàn dải $n$. Ngoài ra, các kiểm thử logic cơ bản (sanity check) cũng phải đạt: với một STA duy nhất thì không có xung đột; tổng thông lượng của các STA bằng thông lượng tổng; độ trễ tăng khi số STA tăng; và kết quả phải tái lập được với cùng hạt giống.

Kết quả số cụ thể của quá trình kiểm chứng được trình bày chi tiết ở Chương 7.
