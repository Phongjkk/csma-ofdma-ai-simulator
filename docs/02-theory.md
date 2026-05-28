# 2. Cơ sở lý thuyết

Chương này trình bày các nền tảng lý thuyết của project: mô hình hoạt động của lớp MAC trong chuẩn IEEE 802.11, hai cơ chế CSMA/CA và OFDMA cùng cách chúng phối hợp với nhau, các chỉ số dùng để đánh giá hiệu năng, và lý thuyết về giám sát mạng cũng như mô hình AI dự đoán chuỗi thời gian.

## 2.1. Mô hình hoạt động của lớp MAC

### 2.1.1. Vai trò của lớp MAC

Trong một mạng không dây ở chế độ hạ tầng, một Access Point (AP) và nhiều Station (STA) cùng chia sẻ một kênh truyền vô tuyến. Vì kênh truyền là dùng chung, cần một cơ chế điều phối để các thiết bị "thay phiên" sử dụng kênh, tránh việc nhiều thiết bị cùng phát gây chồng lấn tín hiệu.

Lớp MAC (Medium Access Control) thuộc tầng liên kết dữ liệu, nằm giữa lớp LLC ở trên và tầng vật lý (PHY) ở dưới, đóng vai trò "trọng tài" quản lý việc truy cập kênh truyền dùng chung. Các chức năng chính của lớp MAC gồm: đóng gói dữ liệu thành khung (frame), điều phối truy cập kênh để tránh xung đột, xác nhận khung nhận được (ACK) và truyền lại khi cần.

Đây cũng chính là tầng mà project tập trung mô phỏng. CSMA/CA là giao thức truy cập kênh thuần túy thuộc lớp MAC; còn OFDMA tuy là kỹ thuật ghép kênh ở tầng vật lý nhưng phần điều phối tài nguyên (phân bổ RU, lập lịch, gửi Trigger Frame) lại do lớp MAC đảm nhiệm — và đó là phần được mô phỏng.

### 2.1.2. Đầu vào và đầu ra của lớp MAC

Vì nằm giữa hai tầng, lớp MAC trao đổi dữ liệu với cả tầng trên và tầng dưới thông qua hai đơn vị dữ liệu:

- **MSDU (MAC Service Data Unit):** gói dữ liệu mà lớp MAC nhận từ tầng trên (LLC). Đây là phần dữ liệu "thô" chưa có thông tin điều khiển của MAC.
- **MPDU (MAC Protocol Data Unit):** khung hoàn chỉnh sau khi lớp MAC bổ sung phần tiêu đề (MAC header chứa địa chỉ nguồn, đích, loại khung, trường thời lượng…) và phần kiểm tra lỗi (FCS – Frame Check Sequence).

Theo hướng phát (transmit), lớp MAC nhận MSDU từ tầng trên, đóng gói thành MPDU rồi áp dụng cơ chế CSMA/CA và OFDMA để đẩy xuống tầng PHY. Theo hướng nhận (receive), lớp MAC nhận MPDU từ PHY, kiểm tra lỗi, gửi ACK và trích phần dữ liệu (MSDU) lên tầng trên.

```
Hướng phát:    MSDU  →  [MAC: + header + FCS]  →  MPDU  →  PHY
Hướng nhận:    PHY   →  MPDU  →  [MAC: gỡ header, kiểm tra FCS]  →  MSDU  →  tầng trên
```

### 2.1.3. Ánh xạ vào mô hình mô phỏng

Trong bộ mô phỏng của project, các khái niệm trên được mô hình hóa ở mức sự kiện và tham số thay vì đến từng byte cụ thể. Cụ thể:

- **Đầu vào** của bộ mô phỏng là các tham số cấu hình: số lượng STA, mức tải, kích thước gói dữ liệu (tương ứng MSDU), các tham số timing của chuẩn 802.11 (SlotTime, SIFS, DIFS, CWmin, CWmax), số lượng đơn vị tài nguyên RU và tham số PHY trừu tượng (data rate, băng thông).
- **Quá trình xử lý** mô phỏng các sự kiện rời rạc: sinh gói, đóng gói thành khung, lắng nghe kênh, backoff, phát khung (hoặc xung đột), chờ ACK, truyền lại.
- **Đầu ra** là năm chỉ số hiệu năng cùng chuỗi thời gian (time series) phục vụ kiểm chứng, trực quan hóa và huấn luyện AI.

Năm chỉ số hiệu năng và công thức tính của chúng được trình bày chi tiết ở mục 2.4.

## 2.2. Cơ chế CSMA/CA

### 2.2.1. Khái niệm

CSMA/CA (Carrier Sense Multiple Access with Collision Avoidance) là cơ chế truy cập kênh cơ bản của chuẩn 802.11. Khác với CSMA/CD dùng trong mạng Ethernet có dây (phát hiện xung đột — Collision Detection), mạng không dây không thể vừa phát vừa lắng nghe trên cùng tần số (chế độ bán song công), do đó không thể phát hiện xung đột trong khi đang truyền. Vì vậy, CSMA/CA chọn hướng *tránh* xung đột (Collision Avoidance) bằng cách lắng nghe kênh trước khi phát và áp dụng cơ chế chờ ngẫu nhiên.

### 2.2.2. Distributed Coordination Function (DCF)

DCF là cơ chế điều phối phân tán, là nền tảng của CSMA/CA trong 802.11. "Phân tán" nghĩa là không có thiết bị trung tâm điều khiển; mỗi STA tự quyết định thời điểm phát dựa trên trạng thái kênh mà nó quan sát được. Quy trình hoạt động của DCF gồm các bước:

1. Khi có khung cần gửi, STA lắng nghe kênh trong khoảng thời gian DIFS.
2. Nếu kênh rảnh suốt khoảng DIFS, STA bắt đầu quá trình backoff. Nếu kênh bận, STA chờ đến khi kênh rảnh trở lại.
3. STA chọn một giá trị backoff ngẫu nhiên trong khoảng [0, CW] và đếm ngược, mỗi SlotTime giảm một đơn vị nếu kênh vẫn rảnh; nếu kênh bận thì tạm dừng đếm.
4. Khi bộ đếm về 0, STA phát khung.
5. Nếu phát thành công, bên nhận gửi lại ACK sau khoảng SIFS. Nếu không nhận được ACK (do xung đột hoặc lỗi), STA coi như thất bại, tăng cửa sổ tranh chấp và truyền lại.

### 2.2.3. Carrier Sensing

STA xác định kênh rảnh hay bận thông qua hai cơ chế cảm nhận sóng mang:

- **Cảm nhận vật lý (physical carrier sensing):** đo mức năng lượng tín hiệu trên kênh thực tế.
- **Cảm nhận ảo (virtual carrier sensing):** dựa trên trường thời lượng (Duration) trong khung mà STA nghe được, cập nhật vào bộ đếm NAV (Network Allocation Vector). Trong thời gian NAV còn lớn hơn 0, STA coi kênh là bận dù không cảm nhận tín hiệu vật lý.

### 2.2.4. Khoảng cách liên khung (IFS)

Các khoảng cách liên khung tạo ra thứ tự ưu tiên truy cập kênh. Khoảng càng ngắn thì mức ưu tiên càng cao:

| Loại IFS | Thời gian điển hình | Mục đích |
|----------|---------------------|----------|
| SIFS | 16 μs | Ngắn nhất, dùng cho ACK và các khung ưu tiên cao |
| DIFS | 34 μs | Khoảng chờ tiêu chuẩn của DCF trước khi truyền |

Vì ACK chỉ cần chờ SIFS (ngắn hơn DIFS), nó luôn được ưu tiên phát trước khi các STA khác kịp bắt đầu một lượt truyền mới, đảm bảo quá trình bắt tay không bị gián đoạn.

### 2.2.5. Thuật toán lùi nhị phân theo cấp số nhân (Binary Exponential Backoff)

Cửa sổ tranh chấp CW (Contention Window) điều chỉnh mức độ "khiêm tốn" của STA khi giành kênh:

- Ban đầu, CW = CWmin (thường là 15).
- Mỗi lần truyền thất bại (không nhận ACK), CW tăng gấp đôi: CW = 2 × CW + 1, cho đến giá trị tối đa CWmax (thường là 1023).
- Sau mỗi lần truyền thành công, CW được đặt lại về CWmin.

| Số lần thất bại | CW | Khoảng chọn backoff |
|-----------------|-----|---------------------|
| 0 | 15 | [0, 15] |
| 1 | 31 | [0, 31] |
| 2 | 63 | [0, 63] |
| 3 | 127 | [0, 127] |
| … | … | … |
| 6 trở lên | 1023 | [0, 1023] |

Việc tăng CW sau mỗi lần xung đột giúp giãn cách thời điểm phát của các STA, giảm xác suất chúng tiếp tục xung đột với nhau.

### 2.2.6. Ưu điểm và hạn chế

CSMA/CA có ưu điểm là đơn giản, phân tán (không cần thiết bị điều khiển trung tâm) và đảm bảo công bằng dài hạn giữa các STA. Tuy nhiên, khi số lượng STA tăng cao, xác suất nhiều STA cùng kết thúc backoff và phát đồng thời tăng lên, dẫn đến số lần xung đột tăng nhanh. Hậu quả là thông lượng giảm, độ trễ tăng vọt và một phần lớn thời gian kênh bị lãng phí cho các lần xung đột. Đây chính là động lực thúc đẩy việc kết hợp thêm cơ chế OFDMA.

## 2.3. Cơ chế OFDMA

### 2.3.1. Khái niệm

OFDMA (Orthogonal Frequency Division Multiple Access) là cơ chế đa truy cập cho phép nhiều STA cùng truyền hoặc nhận song song trên các nhóm sóng mang con khác nhau trong cùng một khoảng thời gian. Đây là điểm khác biệt căn bản so với cách truyền truyền thống, nơi tại mỗi thời điểm chỉ một STA chiếm toàn bộ kênh.

```
Truyền truyền thống (mỗi lúc 1 STA):
┌──────────────────────────────────┐
│            STA A                  │
│      (toàn bộ băng thông)         │
└──────────────────────────────────┘
            tần số →

OFDMA (nhiều STA song song):
┌──────┬──────┬──────┬──────┬──────┐
│ STA A│ STA B│ STA C│ STA D│ STA E│
│  RU  │  RU  │  RU  │  RU  │  RU  │
└──────┴──────┴──────┴──────┴──────┘
            tần số →
```

### 2.3.2. Resource Unit (RU)

Resource Unit là đơn vị tài nguyên nhỏ nhất trong OFDMA, là một nhóm sóng mang con (subcarrier/tone). Một kênh có thể được chia thành nhiều RU với kích thước khác nhau tùy theo số lượng và nhu cầu của các STA.

| Kích thước RU (số tone) | Băng thông tương đương |
|-------------------------|------------------------|
| 26-tone | khoảng 2 MHz |
| 52-tone | khoảng 4 MHz |
| 106-tone | khoảng 8 MHz |
| 242-tone | khoảng 20 MHz (toàn kênh 20 MHz) |

Ví dụ, một kênh 20 MHz (242 tone) có thể chia thành một RU 242-tone (một STA dùng toàn kênh, tương đương cách truyền cũ), hoặc bốn RU 52-tone (bốn STA song song), hoặc chín RU 26-tone (chín STA song song).

### 2.3.3. Trigger Frame và quá trình truyền

Vì STA không tự biết được phép dùng RU nào, AP đóng vai trò điều phối thông qua khung kích hoạt (Trigger Frame). Quy trình truyền hướng lên (uplink OFDMA) diễn ra như sau:

1. AP giành quyền sử dụng kênh thông qua cơ chế CSMA/CA.
2. AP gửi Trigger Frame, trong đó chỉ định STA nào sử dụng RU nào.
3. Sau khoảng SIFS, các STA được chỉ định cùng phát song song trên RU của mình.
4. AP gửi một khung xác nhận gộp (Multi-STA Block ACK) cho tất cả các STA.

Điểm quan trọng là trong vùng OFDMA, các STA **không tự tranh chấp** kênh mà được AP lập lịch. Nhờ đó, xung đột giữa các STA gần như được loại bỏ.

### 2.3.4. Lập lịch (Scheduling)

AP cần quyết định STA nào được cấp RU và kích thước bao nhiêu. Có nhiều thuật toán lập lịch như Round-Robin (luân phiên, công bằng và đơn giản), Proportional Fair (cân bằng giữa thông lượng và công bằng), hay Max-throughput (ưu tiên STA có điều kiện kênh tốt). Project sử dụng thuật toán Round-Robin vì tính đơn giản và đủ để minh họa lợi ích của OFDMA.

### 2.3.5. Sự phối hợp giữa CSMA/CA và OFDMA

Một điểm cần nhấn mạnh là OFDMA **không thay thế** CSMA/CA mà **phối hợp** cùng nó, và đây chính là cơ chế mà project mô phỏng. Trong một chu trình truyền của Wi-Fi 6/7 thực tế, hệ thống hoạt động theo hai giai đoạn:

1. **Giai đoạn giành kênh (CSMA/CA):** AP sử dụng cơ chế CSMA/CA (lắng nghe kênh, DIFS, backoff) để giành quyền sử dụng kênh truyền dùng chung.
2. **Giai đoạn truyền song song (OFDMA):** sau khi giành được kênh, AP gửi Trigger Frame chia kênh thành nhiều RU và lập lịch cho nhiều STA cùng truyền song song.

```
        ┌─────────────────────────────────┐
        │  Giai đoạn 1 — CSMA/CA           │
        │  AP giành kênh                   │
        │  (DIFS + backoff)                │
        └────────────────┬────────────────┘
                         │ giành được kênh
                         ▼
        ┌─────────────────────────────────┐
        │  Giai đoạn 2 — OFDMA             │
        │  Nhiều STA truyền song song      │
        │  trên các RU                     │
        │  (Trigger Frame + parallel TX)   │
        └─────────────────────────────────┘
```

Sự phối hợp này tận dụng được ưu điểm của cả hai cơ chế: AP chỉ cần tranh chấp kênh **một lần** cho cả nhóm (giảm đáng kể overhead tranh chấp so với việc từng STA tự tranh chấp riêng lẻ trong CSMA/CA thuần túy), trong khi nhiều STA được phục vụ **song song** trong cùng một lượt truyền (tăng thông lượng và giảm độ trễ). Nhờ đó, cơ chế kết hợp khắc phục được hạn chế bão hòa của CSMA/CA khi số lượng STA tăng cao — vấn đề đã nêu ở mục 2.2.6.

## 2.4. Các chỉ số hiệu năng

Project đo lường năm chỉ số hiệu năng cốt lõi. Điểm quan trọng về phương pháp: bộ mô phỏng không dùng một công thức kín để tính trực tiếp, mà **đếm và tổng hợp** từ các sự kiện thực tế xảy ra trong quá trình mô phỏng sự kiện rời rạc, sau đó áp dụng các công thức định nghĩa dưới đây.

### 2.4.1. Thông lượng (Throughput)

Thông lượng là lượng bit dữ liệu được truyền **thành công** qua kênh trên một đơn vị thời gian, đo bằng Mbps:

$$
\text{Throughput} = \frac{\text{Tổng số bit truyền thành công}}{\text{Thời gian mô phỏng}}
$$

Chỉ những khung được xác nhận thành công (nhận ACK) mới được tính; các khung bị xung đột không được tính vào thông lượng.

### 2.4.2. Độ trễ (Latency)

Độ trễ của một gói là khoảng thời gian từ khi gói được sinh ra cho đến khi nó được truyền thành công (nhận ACK):

$$
\text{Latency}_i = t_{\text{ACK}} - t_{\text{sinh gói}}
$$

Độ trễ này bao gồm thời gian chờ trong hàng đợi, thời gian backoff, thời gian truyền và thời gian chờ ACK. Project đo hai giá trị: độ trễ trung bình (mean) và độ trễ phân vị 99 (P99 — giá trị mà 99% số gói có độ trễ thấp hơn). Giá trị P99 phản ánh "trường hợp xấu", quan trọng đối với các ứng dụng thời gian thực.

### 2.4.3. Tỷ lệ xung đột (Collision Rate)

Tỷ lệ xung đột là tỷ lệ giữa số lần phát bị xung đột trên tổng số lần phát:

$$
\text{Collision Rate} = \frac{N_{\text{xung đột}}}{N_{\text{xung đột}} + N_{\text{thành công}}}
$$

### 2.4.4. Chỉ số công bằng Jain (Jain's Fairness Index)

Chỉ số công bằng đo mức độ phân chia tài nguyên đồng đều giữa các STA, được tính theo công thức Jain:

$$
J = \frac{\left( \sum_{i=1}^{n} x_i \right)^2}{n \cdot \sum_{i=1}^{n} x_i^2}
$$

trong đó $x_i$ là thông lượng của STA thứ $i$ và $n$ là số STA. Chỉ số $J$ nằm trong khoảng từ $1/n$ đến $1$: giá trị bằng $1$ nghĩa là hoàn toàn công bằng (mọi STA có thông lượng bằng nhau), giá trị càng nhỏ thì sự phân chia càng mất cân bằng.

Ví dụ: với ba STA có thông lượng $[10, 10, 10]$, ta có $J = 30^2 / (3 \times 300) = 1{,}0$ (công bằng tuyệt đối). Với $[28, 1, 1]$, $J = 30^2 / (3 \times 786) \approx 0{,}38$ (rất mất cân bằng).

### 2.4.5. Hiệu suất sử dụng kênh (Channel Utilization)

Hiệu suất sử dụng kênh là phần trăm thời gian kênh được dùng để truyền dữ liệu thành công:

$$
U = \frac{T_{\text{thành công}}}{T_{\text{tổng}}}
$$

Tổng thời gian kênh có thể chia thành ba phần: thời gian truyền thành công, thời gian lãng phí cho xung đột, và thời gian rảnh (idle):

$$
T_{\text{tổng}} = T_{\text{thành công}} + T_{\text{xung đột}} + T_{\text{rảnh}}
$$

Phần thời gian lãng phí cho xung đột chính là yếu tố mà OFDMA giúp giảm thiểu.

### 2.4.6. Cơ sở tính thời gian theo chuẩn 802.11

Mọi chỉ số trên đều phụ thuộc vào việc tính chính xác thời gian truyền theo chuẩn 802.11. Thời gian của một chu trình truyền thành công và một chu trình xung đột được tính như sau:

$$
T_{\text{thành công}} = T_{\text{DIFS}} + T_{\text{backoff}} + T_{\text{khung}} + T_{\text{SIFS}} + T_{\text{ACK}}
$$

$$
T_{\text{xung đột}} = T_{\text{DIFS}} + T_{\text{khung}} + T_{\text{timeout}}
$$

trong đó thời gian truyền phần khung dữ liệu là:

$$
T_{\text{khung}} = T_{\text{PHY}} + \frac{(L_{\text{MAC header}} + L_{\text{payload}} + L_{\text{FCS}}) \times 8}{R_{\text{data}}}
$$

với $L$ là kích thước (byte) của từng thành phần và $R_{\text{data}}$ là tốc độ dữ liệu. Đây là nền tảng để bộ mô phỏng tính toán chính xác các chỉ số và đối chiếu với mô hình toán học Bianchi (trình bày ở Chương 3).

## 2.5. Giám sát mạng theo thời gian thực

### 2.5.1. Khái niệm

Giám sát mạng là quá trình liên tục thu thập và phân tích các chỉ số hiệu năng để đánh giá trạng thái mạng và phát hiện sớm các vấn đề. Mục tiêu là chuyển từ cách tiếp cận bị động (phản ứng sau khi sự cố xảy ra) sang chủ động (phát hiện và xử lý trước).

### 2.5.2. Kỹ thuật cửa sổ trượt (Sliding Window)

Vì mạng tạo ra sự kiện liên tục, không thể lưu trữ và xử lý toàn bộ, kỹ thuật cửa sổ trượt được dùng để chỉ giữ lại và phân tích dữ liệu trong một khoảng thời gian gần nhất (ví dụ 5–10 giây). Cửa sổ này trượt dần theo thời gian, mỗi bước (ví dụ 100 ms) lại tổng hợp dữ liệu thành một mẫu chỉ số. Cách làm này cho phép theo dõi diễn biến chỉ số theo thời gian với chi phí bộ nhớ cố định.

### 2.5.3. Phát hiện bất thường (Anomaly Detection)

Phát hiện bất thường là việc nhận diện các mẫu dữ liệu khác thường so với hành vi bình thường của mạng. Có thể chia thành: bất thường điểm (một giá trị đột biến, ví dụ độ trễ tăng vọt), bất thường theo ngữ cảnh, và bất thường tập thể (một chuỗi giá trị bất thường liên tiếp). Các kỹ thuật phát hiện gồm phương pháp dựa trên ngưỡng (threshold), phương pháp thống kê, và các mô hình học máy như Isolation Forest. Project sử dụng kết hợp phương pháp ngưỡng và Isolation Forest cho mục đích này.

## 2.6. Dự đoán hiệu năng bằng trí tuệ nhân tạo

### 2.6.1. Bài toán dự đoán chuỗi thời gian

Các chỉ số hiệu năng mạng theo thời gian tạo thành một chuỗi thời gian (time series). Bài toán dự đoán đặt ra là: cho biết diễn biến các chỉ số trong một khoảng quá khứ, hãy dự đoán giá trị của chúng trong một khoảng tương lai. Đây là bài toán dự đoán chuỗi thời gian đa biến, nhiều bước (multivariate, multi-step time series forecasting), vì mỗi thời điểm có nhiều chỉ số và cần dự đoán cho nhiều bước phía trước.

Cụ thể trong project, mô hình nhận đầu vào là chuỗi 5 giây quá khứ (50 mẫu với bước 100 ms) của các chỉ số, và dự đoán chuỗi 5 giây tương lai. Từ kết quả dự đoán, hệ thống có thể đưa ra cảnh báo sớm khi dự báo cho thấy mạng sắp rơi vào trạng thái quá tải.

### 2.6.2. Các mô hình dự đoán

Có nhiều nhóm mô hình cho bài toán dự đoán chuỗi thời gian:

- **Nhóm thống kê:** trung bình trượt (Moving Average), ARIMA — đơn giản, phù hợp với chuỗi có quy luật rõ ràng.
- **Nhóm học máy:** hồi quy tuyến tính, Random Forest — mạnh hơn cho dữ liệu phi tuyến.
- **Nhóm học sâu:** RNN, LSTM, GRU, Transformer — phù hợp với chuỗi phức tạp, có khả năng nắm bắt phụ thuộc dài hạn.

Project chọn **LSTM** làm mô hình chính, đồng thời cài đặt các mô hình thống kê và học máy đơn giản làm cơ sở so sánh (baseline).

### 2.6.3. Mạng bộ nhớ dài-ngắn hạn (LSTM)

LSTM (Long Short-Term Memory) là một dạng mạng nơ-ron hồi quy (RNN) được thiết kế để khắc phục vấn đề mất mát gradient của RNN truyền thống, nhờ đó có khả năng "ghi nhớ" thông tin trong khoảng thời gian dài. LSTM sử dụng một trạng thái tế bào (cell state) và ba cổng điều khiển: cổng quên (forget gate) quyết định loại bỏ thông tin cũ nào, cổng vào (input gate) quyết định thông tin mới nào được lưu, và cổng ra (output gate) quyết định thông tin nào được xuất. Cơ chế này giúp LSTM nắm bắt tốt các xu hướng biến động theo thời gian của chỉ số mạng, rất phù hợp cho việc dự đoán hiệu năng.

### 2.6.4. Các chỉ số đánh giá mô hình

Vì đây là bài toán hồi quy (dự đoán giá trị liên tục), độ chính xác của mô hình được đánh giá qua các chỉ số:

| Chỉ số | Ý nghĩa |
|--------|---------|
| MAE (Mean Absolute Error) | Sai số tuyệt đối trung bình giữa giá trị dự đoán và thực tế |
| RMSE (Root Mean Square Error) | Căn bậc hai của sai số bình phương trung bình, phạt nặng các sai số lớn |
| MAPE (Mean Absolute Percentage Error) | Sai số phần trăm tuyệt đối trung bình, cho biết mức sai lệch tương đối |

Một lưu ý quan trọng về phương pháp: với dữ liệu chuỗi thời gian, không được chia tập huấn luyện/kiểm thử một cách ngẫu nhiên vì sẽ làm rò rỉ thông tin từ tương lai vào quá khứ. Thay vào đó, project chia dữ liệu theo trục thời gian hoặc theo kịch bản, đảm bảo mô hình chỉ học từ quá khứ và được kiểm thử trên dữ liệu chưa từng thấy.
