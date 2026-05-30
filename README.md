# CSMA/CA + OFDMA AI Simulator

Bộ mô phỏng mạng không dây IEEE 802.11 kết hợp CSMA/CA và OFDMA, tích hợp hệ thống giám sát thời gian thực và mô hình LSTM dự đoán quá tải mạng.

---

## Mục lục

- [Project làm gì?](#project-làm-gì)
- [Đọc tài liệu lý thuyết trước](#đọc-tài-liệu-lý-thuyết-trước)
- [Cài đặt](#cài-đặt)
- [Chạy nhanh](#chạy-nhanh)
- [Chạy từng phần](#chạy-từng-phần)
- [Kết quả mong đợi](#kết-quả-mong-đợi)
- [Cấu trúc project](#cấu-trúc-project)

---

## Project làm gì?

Project mô phỏng cơ chế truy cập kênh trong mạng Wi-Fi 6 (IEEE 802.11ax) theo ba lớp:

```
┌─────────────────────────────────────────────────┐
│  1. Simulator (DES)                             │
│     CSMA/CA  ──┐                                │
│                ├──► CSMA/CA + OFDMA kết hợp     │
│     OFDMA   ──┘     (như Wi-Fi 6/7 thực tế)    │
├─────────────────────────────────────────────────┤
│  2. Monitoring                                  │
│     Thu thập 5 chỉ số → phát hiện bất thường    │
│     Throughput · Latency · Collision ·          │
│     Fairness · Channel Utilization              │
├─────────────────────────────────────────────────┤
│  3. AI (LSTM)                                   │
│     Nhìn 5s qua → Dự đoán 5s tới               │
│     Cảnh báo sớm khi sắp quá tải               │
└─────────────────────────────────────────────────┘
```

**Kết quả cốt lõi** (đo thực tế, n=20 STA):

| Mức tải | Throughput | Latency P99 | Collision | Channel Busy |
|---------|-----------|-------------|-----------|-------------|
| Thấp    | 4.80 Mbps | 0.70 ms     | 0.0%      | 8.9%        |
| Trung bình | 12.30 Mbps | 1.16 ms  | 0.5%      | 22.9%       |
| Cao     | 34.57 Mbps | 1 557 ms   | 44.6%     | 100%        |

---

## Đọc tài liệu lý thuyết trước

Trước khi chạy, nên đọc tài liệu trong thư mục [`docs/`](docs/) theo thứ tự:

| Chương | File | Nội dung |
|--------|------|---------|
| 1 | [01-introduction.md](docs/01-introduction.md) | Bối cảnh, mục tiêu, phạm vi |
| 2 | [02-theory.md](docs/02-theory.md) | Lý thuyết CSMA/CA, OFDMA, Bianchi |
| 3 | [03-design.md](docs/03-design.md) | Kiến trúc hệ thống, thiết kế DES |
| 4 | [04-implementation.md](docs/04-implementation.md) | Chi tiết cài đặt simulator |
| 5 | [05-monitoring-system.md](docs/05-monitoring-system.md) | Hệ thống giám sát thời gian thực |
| 6 | [06-ai-prediction.md](docs/06-ai-prediction.md) | Mô hình LSTM dự đoán |
| **7** | [**07-evaluation.md**](docs/07-evaluation.md) | **Kết quả đo thực tế** ← đọc sau khi chạy |
| 8 | [08-conclusion.md](docs/08-conclusion.md) | Kết luận, hạn chế, hướng phát triển |

---

## Cài đặt

### Yêu cầu

- Python 3.11+
- pip

### Cài dependencies

```bash
git clone https://github.com/Phongjkk/csma-ofdma-ai-simulator.git
cd csma-ofdma-ai-simulator
pip install -r requirements.txt
```

### Hoặc dùng Docker

```bash
docker-compose up
# Mở trình duyệt: http://localhost:8501
```

---

## Chạy nhanh

### 1. Khởi động dashboard (cách nhanh nhất)

```bash
streamlit run frontend/streamlit_app.py
```

Mở trình duyệt tại **http://localhost:8501**, vào trang **Simulate** và nhấn **Run Simulation**.

---

## Chạy từng phần

### Bước 1 — Chạy mô phỏng đơn lẻ

```python
from simulator.config import SimConfig
from simulator.modes.mode_combined import run_combined

cfg = SimConfig(n_stations=20, traffic_load=0.5, sim_time=30.0, seed=42)
result = run_combined(cfg)

print(result['summary'])
# {'throughput_mbps': 12.3, 'latency_p99_ms': 1.16, 'collision_rate': 0.005, ...}
```

### Bước 2 — Chạy tất cả kịch bản (3 mức tải)

```bash
python -c "
from analysis.runner import run_all_scenarios
results = run_all_scenarios(n_repeats=3, sim_time=30.0)
print(f'Saved {len(results)} results')
"
```

### Bước 3 — Sinh dataset và huấn luyện LSTM

```bash
# Sinh dữ liệu + huấn luyện
python scripts/_train_lstm.py

# Hoặc chỉ sinh dataset
python scripts/generate_dataset.py --runs 3 --out results/datasets/
```

Sau khi train xong, checkpoint được lưu tại `ai/saved_models/lstm_checkpoint.pt`.

### Bước 4 — Chạy demo giám sát thời gian thực

```bash
python scripts/run_live_demo.py --n 20 --load 0.8 --mode combined
```

### Bước 5 — Kiểm chứng Bianchi

```bash
python -c "
from analysis.runner import run_bianchi_validation
report = run_bianchi_validation(n_stations_list=[5, 10, 20, 30])
print('Pass:', report['pass'])
for row in report['validation']:
    print(row)
"
```

### Chạy unit tests

```bash
python -m pytest tests/ -v
```

---

## Kết quả mong đợi

### Sau khi chạy `run_combined()`

```
{
  'throughput_mbps': 12.3,
  'latency_mean_ms': 0.42,
  'latency_p99_ms': 1.16,
  'collision_rate': 0.005,
  'fairness_index': 0.998,
  'channel_util': 0.228,
  'channel_occupancy': 0.229,
  'total_success': 14820,
  'total_collisions': 74
}
```

### Sau khi huấn luyện LSTM

```
Epoch  30/30 | train=0.001440 | val=0.047618

LSTM:           MAE=0.18043  MAPE=31.01%  R²=0.245
Moving Average: MAE=0.01081  MAPE=5.24%   R²=0.996
```

> **Lưu ý:** Trên dữ liệu tổng hợp từ simulator (tín hiệu ổn định),
> Moving Average cho kết quả tốt hơn LSTM vì tín hiệu gần như tuyến tính.
> Trong môi trường Wi-Fi thực tế với traffic động, LSTM sẽ phát huy ưu thế.

### Khi tải cao (load ≥ 2.0)

- `channel_occupancy = 100%` → kênh bão hòa hoàn toàn
- `latency_p99 > 1000ms` → hàng đợi tích lũy (queue buildup)
- Hệ cảnh báo sẽ kích hoạt `CRITICAL` alert

---

## Cấu trúc project

```
csma-ofdma-ai-simulator/
│
├── simulator/          # Bộ mô phỏng DES
│   ├── config.py       # Tham số IEEE 802.11ax
│   ├── core/           # Event scheduler, main loop
│   ├── mac/            # CSMA/CA (DCF) + OFDMA
│   ├── network/        # Station, AccessPoint, Channel, Packet
│   ├── traffic/        # Poisson, CBR, Ramp, Spike generator
│   ├── metrics/        # Thu thập 5 chỉ số hiệu năng
│   └── modes/          # mode_combined (CSMA/CA + OFDMA)
│
├── monitoring/         # Giám sát thời gian thực
│   ├── monitor.py      # Pipeline: buffer → detect → alert
│   ├── anomaly_detector.py  # Threshold + Z-score
│   └── alert_manager.py     # Cooldown, severity
│
├── ai/                 # Pipeline AI
│   ├── models/         # LSTM (PyTorch), Moving Average, LR
│   ├── training/       # Trainer, EarlyStopping, Checkpoint
│   ├── inference/      # StreamPredictor, AlertGenerator
│   └── saved_models/   # Checkpoint LSTM đã train
│
├── analysis/           # Phân tích kết quả
│   ├── runner.py       # Chạy nhiều kịch bản tự động
│   ├── statistics.py   # Mean, CI 95%
│   └── plot_generator.py  # Plotly charts
│
├── frontend/           # Streamlit dashboard (7 trang)
├── docs/               # Tài liệu lý thuyết (8 chương)
├── notebooks/          # Jupyter workflow (7 notebook)
├── scripts/            # CLI: train, generate, demo
├── tests/              # Unit tests
└── docker-compose.yml  # Chạy toàn bộ bằng Docker
```

---

## Công nghệ sử dụng

| Thành phần | Công nghệ |
|------------|-----------|
| Ngôn ngữ | Python 3.11+ |
| Mô phỏng DES | Tự xây dựng (heapq event scheduler) |
| Tính toán | NumPy, SciPy, Pandas |
| Mô hình AI | PyTorch (LSTM), scikit-learn |
| Dashboard | Streamlit + Plotly |
| Triển khai | Docker |

---

## Tác giả

**Phong** — [GitHub @Phongjkk](https://github.com/Phongjkk)
