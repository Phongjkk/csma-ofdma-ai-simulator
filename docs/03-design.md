# 3. Thiết kế hệ thống

Chương này trình bày thiết kế tổng thể của hệ thống: kiến trúc các thành phần và luồng dữ liệu giữa chúng, mô hình toán học Bianchi dùng làm cơ sở kiểm chứng cho bộ mô phỏng, và thiết kế chi tiết của bộ mô phỏng dựa trên kỹ thuật mô phỏng sự kiện rời rạc.

## 3.1. Kiến trúc tổng thể

Hệ thống được chia thành bốn thành phần chính, hoạt động nối tiếp nhau theo luồng dữ liệu từ mô phỏng đến trình diễn:

```
        ┌────────────────────────────┐
        │      BỘ MÔ PHỎNG           │
        │      (Simulator)           │
        │  CSMA/CA + OFDMA, DES      │
        └─────────────┬──────────────┘
                      │  chỉ số, sự kiện
                      ▼
        ┌────────────────────────────┐
        │      GIÁM SÁT              │
        │      (Monitoring)          │
        │  cửa sổ trượt, tổng hợp,   │
        │  phát hiện bất thường      │
        └─────────────┬──────────────┘
                      │  chuỗi thời gian + cảnh báo
                      ▼
        ┌────────────────────────────┐
        │      DỰ ĐOÁN AI            │
        │      (LSTM)                │
        │  huấn luyện, dự đoán 5s,   │
        │  cảnh báo sớm              │
        └─────────────┬──────────────┘
                      │  dự đoán
                      ▼
        ┌────────────────────────────┐
        │      GIAO DIỆN            │
        │      (Dashboard)           │
        │  biểu đồ, cảnh báo realtime│
        └────────────────────────────┘
```

Vai trò của từng thành phần:

- **Bộ mô phỏng (Simulator):** mô phỏng cơ chế CSMA/CA và OFDMA theo chuẩn IEEE 802.11, sinh ra các sự kiện và đo lường năm chỉ số hiệu năng. Đây là thành phần lõi.
- **Giám sát (Monitoring):** thu nhận các chỉ số từ bộ mô phỏng theo thời gian thực, tổng hợp theo cửa sổ trượt và phát hiện bất thường.
- **Dự đoán AI:** sử dụng dữ liệu do bộ mô phỏng sinh ra để huấn luyện mô hình LSTM, sau đó dự đoán hiệu năng và cảnh báo sớm tình trạng quá tải.
- **Giao diện (Dashboard):** trực quan hóa các chỉ số, kết quả dự đoán và cảnh báo, phục vụ theo dõi và trình diễn.

Luồng dữ liệu được chia làm hai pha. Ở **pha ngoại tuyến (offline)**, bộ mô phỏng chạy nhiều kịch bản để sinh tập dữ liệu, sau đó dùng tập dữ liệu này huấn luyện mô hình LSTM. Ở **pha trực tuyến (online)**, bộ mô phỏng chạy theo thời gian thực, đẩy chỉ số sang thành phần giám sát và mô hình AI đã huấn luyện để dự đoán, rồi hiển thị tất cả lên dashboard.

## 3.2. Mô hình toán học Bianchi

### 3.2.1. Mục đích

Trước khi tin tưởng kết quả của bộ mô phỏng, cần có một cơ sở độc lập để kiểm chứng tính đúng đắn của nó. Mô hình Bianchi (đề xuất bởi Giuseppe Bianchi năm 2000) là mô hình toán học kinh điển dùng để phân tích hiệu năng của cơ chế DCF trong chuẩn 802.11, và được xem là chuẩn tham chiếu (gold standard) trong lĩnh vực này.

Ý tưởng kiểm chứng là: tính thông lượng lý thuyết bằng công thức Bianchi, đồng thời đo thông lượng thực tế từ bộ mô phỏng trong cùng điều kiện, rồi so sánh. Nếu hai kết quả trùng khớp (sai số nhỏ), có thể kết luận bộ mô phỏng hoạt động đúng.

### 3.2.2. Các giả định

Mô hình Bianchi đặt ra các giả định sau:

1. Số lượng STA cố định và bằng $n$.
2. Lưu lượng bão hòa (saturated): mỗi STA luôn có khung sẵn sàng để gửi.
3. Kênh truyền lý tưởng: không có lỗi tầng vật lý, mọi thất bại đều do xung đột.
4. Xác suất xung đột $p$ tại mỗi lần phát là không đổi và độc lập (giả thuyết then chốt của Bianchi).
5. Các STA là đồng nhất (cùng tham số CWmin, CWmax).

### 3.2.3. Mô hình chuỗi Markov hai chiều

Bianchi mô hình hóa quá trình backoff của mỗi STA bằng một chuỗi Markov hai chiều với trạng thái $(s, b)$, trong đó $s$ là cấp backoff (số lần đã xung đột, từ $0$ đến $m$) và $b$ là giá trị bộ đếm backoff hiện tại. Cửa sổ tranh chấp ở cấp $s$ là:

$$
W_s = 2^s W_0
$$

với $W_0 = \text{CWmin}$ và cấp tối đa $m$ ứng với $W_m = \text{CWmax}$.

### 3.2.4. Hệ phương trình cốt lõi

Gọi $\tau$ là xác suất một STA phát trong một time slot ngẫu nhiên. Từ phân tích chuỗi Markov, Bianchi đưa ra:

$$
\tau = \frac{2(1 - 2p)}{(1 - 2p)(W_0 + 1) + p W_0 \left(1 - (2p)^m\right)}
$$

Mặt khác, một STA bị xung đột khi có ít nhất một trong $n-1$ STA còn lại cùng phát trong slot đó, nên xác suất xung đột là:

$$
p = 1 - (1 - \tau)^{n - 1}
$$

Hai phương trình trên tạo thành một hệ phi tuyến với hai ẩn $\tau$ và $p$. Hệ này được giải bằng phương pháp số (ví dụ hàm `fsolve` của thư viện SciPy) để tìm ra $\tau$ và $p$ ứng với mỗi giá trị $n$.

### 3.2.5. Công thức thông lượng

Từ $\tau$, ta tính các xác suất trung gian. Xác suất có ít nhất một STA phát trong một slot:

$$
P_{tr} = 1 - (1 - \tau)^n
$$

Xác suất một lần phát là thành công (chỉ đúng một STA phát), với điều kiện có phát:

$$
P_s = \frac{n \tau (1 - \tau)^{n - 1}}{P_{tr}}
$$

Thông lượng bão hòa (saturation throughput) được tính bằng tỷ lệ giữa lượng dữ liệu hữu ích truyền được và độ dài trung bình của một slot:

$$
S = \frac{P_s \, P_{tr} \, E[P]}{(1 - P_{tr})\,\sigma + P_{tr} P_s \, T_s + P_{tr}(1 - P_s)\, T_c}
$$

trong đó:

- $E[P]$ là kích thước payload trung bình (bit);
- $\sigma$ là độ dài một slot rảnh (SlotTime);
- $T_s$ là thời gian một lần phát thành công;
- $T_c$ là thời gian một lần xung đột.

Các giá trị $T_s$ và $T_c$ được tính theo công thức timing đã trình bày ở mục 2.4.6. Mẫu số của công thức biểu diễn độ dài trung bình của một slot, gồm ba khả năng: slot rảnh (không STA nào phát), slot có phát thành công, và slot có xung đột.

### 3.2.6. Kết quả lý thuyết kỳ vọng

Khi áp dụng công thức trên cho các giá trị $n$ tăng dần, mô hình Bianchi cho thấy hai xu hướng quan trọng: xác suất xung đột $p$ tăng dần khi số STA tăng, và do đó thông lượng $S$ đạt đỉnh ở một số lượng STA nhất định rồi suy giảm. Đây chính là biểu hiện định lượng của hiện tượng bão hòa CSMA/CA — cơ sở để so sánh và làm nổi bật lợi ích của việc kết hợp OFDMA. Kết quả số cụ thể và việc đối chiếu với bộ mô phỏng được trình bày ở Chương 4 và Chương 7.

## 3.3. Thiết kế bộ mô phỏng

### 3.3.1. Lựa chọn kỹ thuật mô phỏng sự kiện rời rạc

Hoạt động của mạng là một chuỗi các sự kiện xảy ra tại những thời điểm rời rạc (gói đến, bắt đầu phát, kết thúc phát, xung đột, nhận ACK…). Vì vậy, kỹ thuật **mô phỏng sự kiện rời rạc (Discrete Event Simulation – DES)** là phù hợp nhất. Thay vì tăng thời gian theo từng bước đều đặn (rất tốn kém), DES "nhảy" trực tiếp đến thời điểm của sự kiện kế tiếp, giúp mô phỏng nhanh và chính xác.

Bộ mô phỏng được xây dựng dựa trên thư viện SimPy của Python — một framework chuyên dụng cho DES, cung cấp sẵn cơ chế quản lý đồng hồ mô phỏng, tiến trình và tài nguyên.

### 3.3.2. Các lớp đối tượng chính

Bộ mô phỏng được tổ chức theo hướng đối tượng với các lớp chính sau:

| Lớp | Trách nhiệm |
|-----|-------------|
| `Simulator` | Lớp điều phối tổng thể: khởi tạo cấu hình, chạy vòng lặp sự kiện, thu thập kết quả |
| `AccessPoint` | Mô hình AP: giành kênh bằng CSMA/CA, lập lịch và cấp phát RU cho OFDMA |
| `Station` | Mô hình STA: sinh gói, thực hiện backoff, phát khung trên RU được cấp |
| `Channel` | Mô hình kênh truyền dùng chung: theo dõi trạng thái bận/rảnh, phát hiện xung đột |
| `Packet` | Đơn vị dữ liệu: lưu thời điểm sinh, thời điểm phát thành công (để tính độ trễ) |
| `MetricsCollector` | Thu thập và tổng hợp năm chỉ số hiệu năng |
| `EventScheduler` | Hàng đợi ưu tiên quản lý các sự kiện theo thứ tự thời gian |

### 3.3.3. Các loại sự kiện

Mọi hoạt động trong bộ mô phỏng được biểu diễn dưới dạng sự kiện. Các loại sự kiện chính gồm:

| Sự kiện | Mô tả |
|---------|-------|
| `PacketArrival` | Một gói dữ liệu mới được sinh ra tại một STA |
| `BackoffEnd` | Bộ đếm backoff của một STA về 0, sẵn sàng phát |
| `TransmissionStart` | Một lượt truyền bắt đầu |
| `TransmissionEnd` | Một lượt truyền kết thúc |
| `Collision` | Hai hoặc nhiều STA cùng phát, gây xung đột |
| `AckReceived` | STA nhận được ACK, truyền thành công |
| `TriggerFrame` | AP gửi Trigger Frame để khởi động truyền OFDMA |
| `MetricsTick` | Mốc thời gian định kỳ (mỗi 100 ms) để tổng hợp chỉ số cho giám sát |

Bộ điều phối sự kiện (`EventScheduler`) dùng một hàng đợi ưu tiên (priority queue) để luôn xử lý sự kiện có thời điểm sớm nhất tiếp theo. Sau mỗi sự kiện được xử lý, các sự kiện mới phát sinh sẽ được đưa vào hàng đợi, và đồng hồ mô phỏng được đẩy tới thời điểm của sự kiện kế tiếp.

### 3.3.4. Quy trình một chu trình truyền CSMA/CA + OFDMA

Quy trình mô phỏng một chu trình truyền kết hợp diễn ra như sau:

```
1. Các STA sinh gói (PacketArrival) theo mô hình lưu lượng
        │
        ▼
2. AP thực hiện CSMA/CA để giành kênh
   (lắng nghe DIFS, backoff; nếu xung đột thì tăng CW, thử lại)
        │
        ▼
3. AP giành được kênh, gửi Trigger Frame
   và cấp phát RU cho các STA theo Round-Robin
        │
        ▼
4. Các STA được chọn cùng phát song song trên các RU (OFDMA)
        │
        ▼
5. AP gửi Block ACK xác nhận cho các STA
        │
        ▼
6. MetricsCollector ghi nhận kết quả, quay lại bước 1
```

### 3.3.5. Tham số đầu vào

Bộ mô phỏng nhận các tham số cấu hình sau:

| Nhóm | Tham số | Ý nghĩa |
|------|---------|---------|
| Mạng | `n_stations` | Số lượng STA |
| Lưu lượng | `traffic_load` | Mức tải (thấp / trung bình / cao) |
| Lưu lượng | `traffic_pattern` | Mẫu sinh lưu lượng (Poisson / CBR) |
| Lưu lượng | `payload_size` | Kích thước gói dữ liệu (byte) |
| PHY | `data_rate` | Tốc độ dữ liệu |
| PHY | `channel_bandwidth` | Băng thông kênh |
| MAC | `cw_min`, `cw_max` | Cửa sổ tranh chấp tối thiểu/tối đa |
| MAC | `slot_time`, `sifs`, `difs` | Các tham số timing |
| OFDMA | `n_ru` | Số đơn vị tài nguyên RU |
| Mô phỏng | `sim_time` | Thời lượng mô phỏng (giây) |
| Mô phỏng | `seed` | Hạt giống ngẫu nhiên (đảm bảo tái lập) |

### 3.3.6. Định dạng đầu ra

Sau khi chạy, bộ mô phỏng xuất kết quả dưới dạng có cấu trúc (JSON), gồm ba phần:

- **Phần cấu hình (config):** lưu lại các tham số đã dùng, phục vụ tái lập.
- **Phần tổng hợp (summary):** giá trị cuối cùng của năm chỉ số hiệu năng cho cả lần chạy.
- **Phần chuỗi thời gian (time series):** giá trị của năm chỉ số tại mỗi mốc 100 ms, phục vụ trực quan hóa và huấn luyện AI.

```
{
  "config":  { n_stations, traffic_load, n_ru, seed, ... },
  "summary": { throughput, latency_mean, latency_p99,
               collision_rate, fairness, channel_utilization },
  "time_series": [
      { "t": 0.1, "throughput": ..., "collision_rate": ..., ... },
      { "t": 0.2, "throughput": ..., "collision_rate": ..., ... },
      ...
  ]
}
```

Định dạng này được dùng thống nhất cho cả ba mục đích: đối chiếu với mô hình Bianchi để kiểm chứng, vẽ biểu đồ trên dashboard, và tạo tập dữ liệu huấn luyện cho mô hình AI.
