# 7. Đánh giá kết quả

Chương này trình bày kết quả đánh giá toàn hệ thống: tính đúng đắn của bộ mô phỏng (đối chiếu Bianchi), hiệu năng của hệ CSMA/CA + OFDMA qua các mức tải, độ chính xác của mô hình AI, và hiệu quả của hệ thống cảnh báo.

> Lưu ý: Các bảng số liệu trong chương này là khuôn mẫu để điền kết quả thực tế sau khi chạy mô phỏng và huấn luyện. Các giá trị minh họa thể hiện xu hướng kỳ vọng, cần được thay bằng số đo thực tế của project.

## 7.1. Đánh giá bộ mô phỏng

### 7.1.1. Đối chiếu với mô hình Bianchi

Tiêu chí quan trọng nhất để đánh giá bộ mô phỏng là sự trùng khớp với mô hình toán học Bianchi. Bảng dưới so sánh thông lượng đo từ bộ mô phỏng (chế độ chỉ CSMA/CA, lưu lượng bão hòa) với thông lượng tính theo công thức Bianchi:

| Số STA ($n$) | Bianchi (Mbps) | Mô phỏng (Mbps) | Sai số (%) |
|--------------|----------------|------------------|------------|
| 5 | _(điền)_ | _(điền)_ | _(điền)_ |
| 10 | | | |
| 20 | | | |
| 30 | | | |
| 50 | | | |
| 75 | | | |
| 100 | | | |

Tiêu chí đạt: sai số tương đối trung bình dưới 3% trên toàn dải $n$. Khi vẽ chồng hai đường (lý thuyết và mô phỏng) lên cùng một biểu đồ, hai đường cần trùng khít, cho thấy bộ mô phỏng tái hiện đúng hành vi lý thuyết của CSMA/CA.

### 7.1.2. Kiểm thử logic (sanity checks)

Bên cạnh đối chiếu định lượng, bộ mô phỏng cần vượt qua các kiểm thử logic:

| Kiểm thử | Kỳ vọng |
|----------|---------|
| Một STA duy nhất | Không có xung đột, thông lượng gần tối đa |
| Tổng thông lượng các STA | Bằng thông lượng tổng đo được |
| Tăng số STA | Độ trễ trung bình tăng |
| Cùng hạt giống ngẫu nhiên | Kết quả tái lập chính xác |

### 7.1.3. Hiệu năng thực thi

Cần ghi nhận thời gian thực thi để chứng minh bộ mô phỏng đủ nhanh cho việc sinh dữ liệu quy mô lớn. Mục tiêu: mô phỏng 30 giây hoạt động mạng hoàn thành trong dưới 10 giây thực thi.

## 7.2. Đánh giá hiệu năng hệ CSMA/CA + OFDMA

### 7.2.1. Phương pháp đánh giá

Vì hệ thống mô phỏng cơ chế CSMA/CA + OFDMA kết hợp, việc đánh giá tập trung vào diễn biến hiệu năng khi **mức tải tăng dần**: tăng số lượng STA và tăng lưu lượng. Đồng thời, kết quả được đối chiếu với **đường giới hạn lý thuyết của CSMA/CA thuần túy** (tính từ mô hình Bianchi) để làm nổi bật lợi ích mà OFDMA mang lại.

Ba mức tải được xem xét:

| Mức tải | Đặc điểm | Mục đích đánh giá |
|---------|----------|-------------------|
| Thấp | Ít STA, lưu lượng nhỏ | Kiểm tra hệ hoạt động đúng khi nhàn rỗi |
| Trung bình | Số STA vừa, lưu lượng vừa | Đánh giá hiệu năng trong điều kiện thường |
| Cao | Nhiều STA, lưu lượng lớn | Đánh giá khả năng chống bão hòa |

### 7.2.2. Diễn biến các chỉ số theo mức tải

Bảng khuôn mẫu ghi nhận năm chỉ số của hệ kết hợp ở các mức tải khác nhau:

| Mức tải | Throughput (Mbps) | Latency P99 (ms) | Collision (%) | Fairness | Channel util (%) |
|---------|-------------------|------------------|---------------|----------|------------------|
| Thấp | _(điền)_ | | | | |
| Trung bình | | | | | |
| Cao | | | | | |

### 7.2.3. So sánh với giới hạn lý thuyết CSMA/CA

Điểm đánh giá quan trọng nhất: ở mức tải cao, CSMA/CA thuần túy (theo Bianchi) bị bão hòa — thông lượng không tăng được nữa, độ trễ và tỷ lệ xung đột tăng vọt. Hệ CSMA/CA + OFDMA được kỳ vọng vượt qua giới hạn này nhờ cho phép nhiều STA truyền song song, nhờ đó duy trì thông lượng cao và độ trễ thấp ngay cả khi số STA lớn.

```
Throughput
(Mbps)
   ▲
   │                  ___________  CSMA/CA + OFDMA
   │              ___/             (duy trì cao)
   │          ___/
   │      ___/      ___________
   │   __/      ___/            CSMA/CA thuần túy
   │ _/    ___/                 (Bianchi: bão hòa rồi giảm)
   │/  ___/
   └──────────────────────────────►  Số STA
```

Khoảng cách giữa hai đường ở vùng tải cao chính là **lợi ích định lượng của OFDMA** — kết quả cốt lõi của project.

## 7.3. Đánh giá mô hình AI

### 7.3.1. So sánh với các mô hình cơ sở

Độ chính xác của LSTM được so sánh với các baseline trên cùng tập kiểm thử, qua ba chỉ số MAE, RMSE, MAPE:

| Mô hình | MAE | RMSE | MAPE (%) | Thời gian suy luận (ms) |
|---------|-----|------|----------|--------------------------|
| Trung bình trượt | _(điền)_ | | | |
| Hồi quy tuyến tính | | | | |
| ARIMA | | | | |
| **LSTM** | | | | |

Kỳ vọng: LSTM cho sai số thấp hơn đáng kể so với các baseline, chứng minh giá trị của mô hình học sâu cho bài toán này.

### 7.3.2. Độ chính xác theo tầm dự đoán

Vì mô hình dự đoán 50 bước (5 giây), độ chính xác thường giảm dần theo tầm dự đoán xa hơn. Bảng dưới ghi nhận xu hướng này:

| Tầm dự đoán | MAE | MAPE (%) |
|-------------|-----|----------|
| 1 giây | _(điền)_ | |
| 3 giây | | |
| 5 giây | | |

Mục tiêu: ngay cả ở tầm 5 giây, sai số vẫn đủ nhỏ để cảnh báo có giá trị thực tiễn.

## 7.4. Đánh giá hệ thống cảnh báo

Khả năng cảnh báo sớm quá tải được đánh giá như một bài toán phân loại: dự báo có/không xảy ra quá tải trong 5 giây tới. Các chỉ số đánh giá:

| Chỉ số | Ý nghĩa | Kết quả |
|--------|---------|---------|
| Precision | Tỷ lệ cảnh báo đúng trên tổng số cảnh báo | _(điền)_ |
| Recall | Tỷ lệ sự kiện quá tải được phát hiện | |
| F1-score | Trung bình điều hòa của precision và recall | |
| Tỷ lệ cảnh báo giả | Cảnh báo sai khi mạng vẫn bình thường | |

Mục tiêu: hệ thống phát hiện được phần lớn các sự kiện quá tải trước 5 giây với tỷ lệ cảnh báo giả thấp.

## 7.5. Tổng hợp kết quả

Phần này tổng hợp các kết quả chính của project, đối chiếu với các mục tiêu đề ra ở Chương 1:

| Mục tiêu | Tiêu chí | Kết quả |
|----------|----------|---------|
| Mô phỏng CSMA/CA đúng | Sai số Bianchi < 3% | _(điền)_ |
| Mô phỏng OFDMA | Truyền song song nhiều STA | |
| Đo 5 chỉ số hiệu năng | Đầy đủ 5 chỉ số | |
| Hệ kết hợp vượt giới hạn CSMA/CA | Thông lượng cao hơn ở tải cao | |
| Sinh tập dữ liệu | Khoảng 300.000 mẫu | |
| Mô hình AI dự đoán | Tốt hơn baseline | |
| Cảnh báo sớm | F1 cao, ít cảnh báo giả | |
| Giao diện trực quan | Dashboard thời gian thực | |

Việc điền đầy đủ bảng này bằng số liệu thực tế sẽ tạo nên bức tranh hoàn chỉnh về mức độ hoàn thành mục tiêu của project.
