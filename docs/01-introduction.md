# 1. Giới thiệu

## 1.1. Bối cảnh và vấn đề

Mạng cục bộ không dây (Wireless LAN) dựa trên họ chuẩn IEEE 802.11 (Wi-Fi) là phương thức kết nối phổ biến nhất hiện nay, hiện diện từ gia đình, văn phòng cho đến các khu vực công cộng mật độ cao như sân bay hay sân vận động. Cùng với sự bùng nổ của thiết bị di động, thiết bị IoT và các ứng dụng đòi hỏi băng thông lớn, độ trễ thấp (video 4K/8K, hội nghị trực tuyến, game thời gian thực, thực tế ảo/tăng cường), số lượng thiết bị cùng chia sẻ một điểm truy cập (Access Point) ngày càng tăng.

Đặc thù của mạng không dây là **kênh truyền dùng chung**: tại một thời điểm và trên cùng một dải tần, nếu nhiều thiết bị cùng phát thì tín hiệu sẽ chồng lấn và gây ra **xung đột (collision)**, khiến dữ liệu phải truyền lại. Để giải quyết vấn đề này, chuẩn 802.11 truyền thống sử dụng cơ chế **CSMA/CA (Carrier Sense Multiple Access with Collision Avoidance)** — mỗi thiết bị phải lắng nghe kênh và chờ theo cơ chế ngẫu nhiên trước khi phát nhằm *tránh* xung đột. Cơ chế này hoạt động ổn định khi số lượng thiết bị ít, nhưng khi mật độ thiết bị tăng cao, số lần xung đột tăng nhanh, dẫn đến **suy giảm thông lượng, tăng độ trễ và lãng phí tài nguyên kênh truyền**.

Để khắc phục, chuẩn IEEE 802.11ax (Wi-Fi 6) và 802.11be (Wi-Fi 7) đưa vào cơ chế **OFDMA (Orthogonal Frequency Division Multiple Access)**, cho phép chia một kênh tần số thành nhiều đơn vị tài nguyên nhỏ (Resource Unit – RU) để **nhiều thiết bị truyền song song** trong cùng một lần truyền, dưới sự điều phối của Access Point. OFDMA không thay thế mà **bổ sung** cho CSMA/CA, giúp giảm tranh chấp kênh và nâng cao hiệu năng ở môi trường đông thiết bị.

Hiệu năng thực tế của mạng không dây phụ thuộc vào nhiều yếu tố biến động theo thời gian (số lượng thiết bị, lưu lượng, mẫu sinh lưu lượng…). Việc **giám sát hiệu năng theo thời gian thực** và **dự đoán sớm tình trạng quá tải** trước khi nó xảy ra sẽ giúp hệ thống chủ động điều chỉnh thay vì chỉ phản ứng sau khi sự cố đã diễn ra. Đây là hướng ứng dụng trí tuệ nhân tạo (AI) đang được quan tâm trong lĩnh vực mạng máy tính.

Từ những vấn đề trên, project này thực hiện **mô phỏng cơ chế CSMA/CA và OFDMA**, đánh giá định lượng hiệu năng của chúng, đồng thời xây dựng **hệ thống giám sát kết hợp mô hình AI để dự đoán hiệu năng theo thời gian thực**.

## 1.2. Mục tiêu

### 1.2.1. Mục tiêu tổng quát

Xây dựng hệ thống mô phỏng cơ chế truy cập kênh CSMA/CA và cơ chế đa truy cập OFDMA trong mạng không dây IEEE 802.11, kết hợp công cụ giám sát và mô hình AI nhằm phân tích, đánh giá và dự đoán hiệu năng mạng theo thời gian thực.

### 1.2.2. Mục tiêu cụ thể

1. Mô phỏng chính xác cơ chế CSMA/CA (DCF) theo chuẩn IEEE 802.11: lắng nghe kênh, khoảng cách liên khung (IFS), thuật toán lùi ngẫu nhiên (backoff) và cơ chế xác nhận (ACK).
2. Mô phỏng cơ chế OFDMA: phân bổ Resource Unit, Trigger Frame và truyền song song nhiều thiết bị.
3. Mô phỏng cơ chế CSMA/CA + OFDMA kết hợp như trong Wi-Fi 6/7 thực tế, và đánh giá hiệu năng của hệ thống qua các mức tải khác nhau.
4. Đo lường năm chỉ số hiệu năng cốt lõi: thông lượng (throughput), độ trễ (latency), tỷ lệ xung đột (collision rate), chỉ số công bằng (fairness index) và hiệu suất sử dụng kênh (channel utilization).
5. Kiểm chứng tính đúng đắn của bộ mô phỏng bằng cách đối chiếu với mô hình toán học Bianchi.
6. Sinh tập dữ liệu hiệu năng từ bộ mô phỏng để huấn luyện mô hình AI.
7. Xây dựng mô hình học sâu (LSTM) dự đoán hiệu năng và cảnh báo sớm tình trạng quá tải.
8. Phát triển giao diện trực quan (dashboard) cho phép theo dõi và demo hệ thống theo thời gian thực.

## 1.3. Phạm vi

### 1.3.1. Phạm vi về tầng giao thức

Trong mô hình phân tầng của chuẩn IEEE 802.11, project tập trung mô phỏng ở **tầng liên kết dữ liệu (Data Link Layer), cụ thể là lớp con điều khiển truy cập môi trường (MAC – Medium Access Control)**:

- **CSMA/CA** là giao thức truy cập kênh thuần túy thuộc lớp MAC. Project mô phỏng đầy đủ: carrier sensing, backoff, contention window, các khoảng IFS (SIFS/DIFS), NAV và ACK.
- **OFDMA** về bản chất là kỹ thuật ghép kênh ở tầng vật lý (PHY), nhưng việc *điều phối tài nguyên* — phân bổ RU, gửi Trigger Frame, lập lịch cho các thiết bị — do lớp MAC đảm nhiệm. Project mô phỏng phần điều phối này ở lớp MAC.
- **Tầng vật lý (PHY)** chỉ được mô hình hóa ở **mức trừu tượng** thông qua các tham số như tốc độ dữ liệu (data rate), băng thông kênh và băng thông mỗi RU; project không đi sâu vào điều chế tín hiệu (QAM), mã hóa kênh hay mô hình kênh truyền vật lý.

### 1.3.2. Nội dung trong phạm vi

- Mô phỏng tầng MAC của IEEE 802.11 với cơ chế CSMA/CA và OFDMA.
- Cấu hình mạng gồm một Access Point và nhiều Station.
- Mô hình lưu lượng theo phân phối Poisson và lưu lượng cố định (CBR).
- Ba mức tải: thấp, trung bình và cao.
- Bài toán AI thuộc dạng dự đoán chuỗi thời gian (time series forecasting) cho các chỉ số hiệu năng.

### 1.3.3. Nội dung ngoài phạm vi

- Tầng vật lý chi tiết: điều chế, mã hóa kênh, MIMO, beamforming.
- Tính di động của thiết bị (mobility).
- Mạng nhiều AP hoặc mạng mesh.
- Các tính năng đặc trưng riêng của Wi-Fi 7: Multi-Link Operation (MLO), Multi-RU, Preamble Puncturing.

## 1.4. Phương pháp thực hiện

1. **Nghiên cứu lý thuyết:** Tìm hiểu chuẩn IEEE 802.11, cơ chế CSMA/CA, OFDMA và các công trình liên quan về giám sát, dự đoán hiệu năng mạng.
2. **Phân tích toán học:** Áp dụng mô hình Bianchi để tính thông lượng và xác suất xung đột lý thuyết, làm cơ sở kiểm chứng.
3. **Xây dựng mô phỏng:** Phát triển bộ mô phỏng dựa trên kỹ thuật mô phỏng sự kiện rời rạc (Discrete Event Simulation – DES) bằng Python.
4. **Kiểm chứng (validation):** So sánh kết quả mô phỏng với mô hình Bianchi để đảm bảo tính đúng đắn.
5. **Sinh dữ liệu:** Chạy bộ mô phỏng với nhiều kịch bản đa dạng để tạo tập dữ liệu hiệu năng dạng chuỗi thời gian.
6. **Huấn luyện AI:** Xây dựng và huấn luyện mô hình LSTM, so sánh với các mô hình cơ sở (baseline).
7. **Đánh giá:** Phân tích hiệu năng qua các chế độ và mức tải, đánh giá độ chính xác của mô hình AI.

## 1.5. Công nghệ sử dụng

| Thành phần | Công nghệ |
|------------|-----------|
| Ngôn ngữ | Python 3.11+ |
| Mô phỏng (DES) | SimPy |
| Tính toán, xử lý dữ liệu | NumPy, Pandas, SciPy |
| Mô hình AI | PyTorch (LSTM), scikit-learn, statsmodels |
| API thời gian thực | FastAPI, WebSocket |
| Giao diện (dashboard) | Streamlit |
| Trực quan hóa | Matplotlib, Plotly |
| Triển khai | Docker |

## 1.6. Cấu trúc tài liệu

- **Phần 1 – Giới thiệu:** Bối cảnh, mục tiêu, phạm vi và phương pháp thực hiện.
- **Phần 2 – Cơ sở lý thuyết:** Mạng không dây IEEE 802.11, cơ chế CSMA/CA, OFDMA, lý thuyết giám sát mạng và mô hình AI dự đoán chuỗi thời gian.
- **Phần 3 – Thiết kế hệ thống:** Kiến trúc tổng thể, mô hình toán học (Bianchi) và thiết kế bộ mô phỏng.
- **Phần 4 – Triển khai mô phỏng:** Cài đặt CSMA/CA, OFDMA và quá trình kiểm chứng với lý thuyết.
- **Phần 5 – Hệ thống giám sát:** Cơ chế thu thập, tổng hợp chỉ số và phát hiện bất thường theo thời gian thực.
- **Phần 6 – Dự đoán bằng AI:** Bài toán, sinh dữ liệu, xây dựng và huấn luyện mô hình dự đoán.
- **Phần 7 – Đánh giá kết quả:** Trình bày và phân tích kết quả mô phỏng và dự đoán.
- **Phần 8 – Kết luận:** Tổng kết kết quả, hạn chế và hướng phát triển.

## 1.7. Danh mục từ viết tắt

| Từ viết tắt | Tiếng Anh đầy đủ | Ý nghĩa |
|-------------|------------------|---------|
| AP | Access Point | Điểm truy cập |
| STA | Station | Thiết bị trạm (thiết bị đầu cuối) |
| WLAN | Wireless Local Area Network | Mạng cục bộ không dây |
| MAC | Medium Access Control | Điều khiển truy cập môi trường |
| PHY | Physical Layer | Tầng vật lý |
| CSMA/CA | Carrier Sense Multiple Access with Collision Avoidance | Đa truy cập cảm nhận sóng mang có tránh xung đột |
| OFDMA | Orthogonal Frequency Division Multiple Access | Đa truy cập phân chia theo tần số trực giao |
| DCF | Distributed Coordination Function | Hàm điều phối phân tán |
| RU | Resource Unit | Đơn vị tài nguyên |
| IFS | Inter-Frame Space | Khoảng cách liên khung |
| SIFS | Short Inter-Frame Space | Khoảng liên khung ngắn |
| DIFS | DCF Inter-Frame Space | Khoảng liên khung của DCF |
| NAV | Network Allocation Vector | Vector phân bổ mạng |
| ACK | Acknowledgement | Khung xác nhận |
| CW | Contention Window | Cửa sổ tranh chấp |
| DES | Discrete Event Simulation | Mô phỏng sự kiện rời rạc |
| AI | Artificial Intelligence | Trí tuệ nhân tạo |
| LSTM | Long Short-Term Memory | Mạng bộ nhớ dài-ngắn hạn |
| MAE | Mean Absolute Error | Sai số tuyệt đối trung bình |
| RMSE | Root Mean Square Error | Căn bậc hai sai số bình phương trung bình |
| MAPE | Mean Absolute Percentage Error | Sai số phần trăm tuyệt đối trung bình |
