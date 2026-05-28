# 6. Dự đoán bằng AI

Chương này trình bày thành phần trí tuệ nhân tạo của project: phát biểu bài toán dự đoán, cách sinh tập dữ liệu từ bộ mô phỏng, tiền xử lý và trích xuất đặc trưng, kiến trúc và huấn luyện mô hình LSTM, cuối cùng là dự đoán thời gian thực kèm cảnh báo sớm.

## 6.1. Phát biểu bài toán

Bài toán đặt ra là dự đoán diễn biến hiệu năng mạng trong tương lai gần dựa trên dữ liệu quá khứ. Cụ thể, mô hình nhận chuỗi các chỉ số trong $N$ bước quá khứ và dự đoán chuỗi chỉ số trong $M$ bước tương lai:

$$
X_t = \{ m_{t-N+1}, m_{t-N+2}, \dots, m_t \} \quad \longrightarrow \quad \hat{Y}_t = \{ \hat{m}_{t+1}, \hat{m}_{t+2}, \dots, \hat{m}_{t+M} \}
$$

trong đó $m_i$ là vector các chỉ số hiệu năng tại thời điểm $i$. Project chọn $N = M = 50$, tương ứng 5 giây quá khứ và 5 giây tương lai (mỗi bước 100 ms). Đây là bài toán dự đoán chuỗi thời gian đa biến, nhiều bước.

Từ kết quả dự đoán $\hat{Y}_t$, hệ thống sinh cảnh báo sớm nếu dự báo cho thấy một chỉ số sắp vượt ngưỡng nguy hiểm (ví dụ hiệu suất sử dụng kênh được dự báo vượt 95% trong vài giây tới).

## 6.2. Sinh tập dữ liệu

### 6.2.1. Nguồn dữ liệu

Một câu hỏi cốt lõi là: dữ liệu để huấn luyện mô hình AI lấy từ đâu? Project sử dụng **dữ liệu tổng hợp (synthetic data) sinh ra từ chính bộ mô phỏng**, thay vì thu thập từ mạng Wi-Fi thật.

Lựa chọn này dựa trên các lý do sau. Về mặt thực tế, việc thu thập dữ liệu thật đòi hỏi thiết bị đo chuyên dụng, một mạng thử nghiệm với nhiều thiết bị, và thời gian dài để có đủ dữ liệu đa dạng — vượt quá điều kiện của project. Về mặt khoa học, dữ liệu từ bộ mô phỏng có ưu điểm là đa dạng (tự tạo nhiều kịch bản), có nhãn chính xác (biết rõ trạng thái mạng tại mọi thời điểm), cân bằng và tái lập được. Quan trọng nhất, bộ mô phỏng đã được kiểm chứng với mô hình Bianchi (sai số dưới 3%), nên dữ liệu nó sinh ra là đáng tin cậy. Đây cũng là cách tiếp cận phổ biến trong nhiều nghiên cứu về AI cho mạng, vốn thường dùng các bộ mô phỏng như ns-3 hay OMNeT++ để sinh dữ liệu huấn luyện.

### 6.2.2. Quy trình sinh dữ liệu

Tập dữ liệu được tạo bằng cách chạy bộ mô phỏng trên nhiều kịch bản đa dạng:

```
Bước 1: Định nghĩa các kịch bản đa dạng
        - Số STA: 5, 10, 20, 30, 50, 75, 100
        - Mẫu tải: không đổi, tăng dần, đột biến, dao động
        → khoảng 100 kịch bản
Bước 2: Mỗi kịch bản chạy nhiều lần với hạt giống khác nhau (vd 10 lần)
        → khoảng 1000 lần chạy
Bước 3: Mỗi lần chạy 30 giây, thu mẫu mỗi 100 ms
        → 300 mẫu/lần
Bước 4: Tổng hợp → khoảng 300.000 mẫu, lưu dạng CSV/Parquet
```

Đặc biệt, các mẫu tải biến đổi theo thời gian (tăng dần, đột biến, dao động) rất quan trọng, vì chúng giúp mô hình học được cách nhận diện xu hướng dẫn tới quá tải.

### 6.2.3. Cấu trúc dữ liệu

Mỗi mẫu trong tập dữ liệu là một bản ghi gồm thông tin kịch bản và giá trị các chỉ số tại một thời điểm:

| Trường | Mô tả |
|--------|-------|
| `scenario_id`, `run_id`, `timestamp` | Định danh kịch bản, lần chạy, mốc thời gian |
| `n_stations`, `traffic_load` | Bối cảnh (số STA, mức tải hiện tại) |
| `throughput_mbps` | Thông lượng |
| `latency_mean_ms`, `latency_p99_ms` | Độ trễ trung bình và P99 |
| `collision_rate` | Tỷ lệ xung đột |
| `fairness_index` | Chỉ số công bằng |
| `channel_utilization` | Hiệu suất sử dụng kênh |

## 6.3. Tiền xử lý và trích xuất đặc trưng

### 6.3.1. Chuẩn hóa

Các chỉ số có thang đo rất khác nhau (thông lượng hàng trăm Mbps, tỷ lệ xung đột trong khoảng 0–1), nên cần chuẩn hóa về cùng một thang trước khi đưa vào mô hình. Project dùng chuẩn hóa Min-Max hoặc Standard (z-score), và lưu lại bộ chuẩn hóa để áp dụng nhất quán khi dự đoán.

### 6.3.2. Trích xuất đặc trưng

Ngoài các chỉ số thô, project tạo thêm các đặc trưng giúp mô hình nắm bắt xu hướng tốt hơn:

- **Đặc trưng thống kê trượt:** trung bình, độ lệch chuẩn trên các cửa sổ 1 giây, 3 giây.
- **Đặc trưng xu hướng:** độ biến thiên (đạo hàm rời rạc) của chỉ số — đây là nhóm đặc trưng quan trọng nhất để dự báo quá tải, vì nó cho biết chỉ số đang tăng hay giảm.
- **Đặc trưng trễ (lag):** giá trị của chỉ số ở các bước trước.

### 6.3.3. Tạo chuỗi và chia tập dữ liệu

Dữ liệu được cắt thành các cặp (chuỗi đầu vào 50 bước, chuỗi đầu ra 50 bước) bằng kỹ thuật cửa sổ trượt. Một điểm quan trọng về phương pháp: việc chia tập huấn luyện/kiểm thử **không được làm ngẫu nhiên** vì sẽ làm rò rỉ thông tin tương lai. Thay vào đó, project chia **theo kịch bản** — các kịch bản dùng để huấn luyện hoàn toàn tách biệt với các kịch bản dùng để kiểm thử (ví dụ 70% kịch bản cho huấn luyện, 15% cho kiểm định, 15% cho kiểm thử).

## 6.4. Kiến trúc mô hình LSTM

Mô hình chính là một mạng LSTM nhiều tầng, nhận chuỗi đầu vào và xuất ra chuỗi dự đoán:

```
        ┌────────────────────────────────┐
        │  Đầu vào                       │
        │  (batch, 50, số đặc trưng)     │
        └───────────────┬────────────────┘
                        ▼
        ┌────────────────────────────────┐
        │  LSTM tầng 1 (hidden = 64)     │
        └───────────────┬────────────────┘
                        ▼
        ┌────────────────────────────────┐
        │  Dropout (0.2)                 │
        └───────────────┬────────────────┘
                        ▼
        ┌────────────────────────────────┐
        │  LSTM tầng 2 (hidden = 64)     │
        └───────────────┬────────────────┘
                        ▼
        ┌────────────────────────────────┐
        │  Tầng kết nối đầy đủ (Dense)   │
        └───────────────┬────────────────┘
                        ▼
        ┌────────────────────────────────┐
        │  Đầu ra                        │
        │  (batch, 50, số chỉ số)        │
        └────────────────────────────────┘
```

Cài đặt bằng PyTorch:

```python
import torch.nn as nn

class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden=64, layers=2,
                 out_steps=50, out_features=6):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden, layers,
                            batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden, out_steps * out_features)
        self.out_steps = out_steps
        self.out_features = out_features

    def forward(self, x):
        out, _ = self.lstm(x)
        last = out[:, -1, :]                 # trạng thái ẩn cuối
        y = self.fc(last)
        return y.view(-1, self.out_steps, self.out_features)
```

Bên cạnh LSTM, project cài đặt thêm các mô hình cơ sở (baseline) để so sánh: trung bình trượt, hồi quy tuyến tính và ARIMA. Việc so sánh này nhằm chứng minh giá trị thực sự của mô hình học sâu so với các phương pháp đơn giản hơn.

## 6.5. Huấn luyện mô hình

Quá trình huấn luyện sử dụng hàm mất mát MSE (sai số bình phương trung bình) và thuật toán tối ưu Adam. Vòng lặp huấn luyện gồm các kỹ thuật chuẩn để đảm bảo hội tụ ổn định và tránh quá khớp (overfitting):

- **Cắt gradient (gradient clipping):** tránh hiện tượng bùng nổ gradient thường gặp ở mạng hồi quy.
- **Điều chỉnh tốc độ học (learning rate scheduling):** giảm tốc độ học khi mất mát kiểm định ngừng cải thiện.
- **Dừng sớm (early stopping):** dừng huấn luyện khi mô hình không còn tiến bộ trên tập kiểm định, đồng thời lưu lại mô hình tốt nhất.

```python
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
criterion = nn.MSELoss()

for epoch in range(EPOCHS):
    model.train()
    for X, y in train_loader:
        optimizer.zero_grad()
        loss = criterion(model(X), y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
    # ... đánh giá trên tập kiểm định, early stopping
```

Việc huấn luyện có thể thực hiện trên CPU, nhưng nhanh hơn nhiều trên GPU; với tập dữ liệu khoảng 300.000 mẫu, thời gian huấn luyện trên GPU phổ thông chỉ vào khoảng vài chục phút.

## 6.6. Dự đoán thời gian thực và cảnh báo

Sau khi huấn luyện, mô hình được nạp vào một bộ dự đoán hoạt động cùng hệ thống giám sát. Mỗi khi có đủ 50 mẫu gần nhất trong bộ đệm, bộ dự đoán tính ra chuỗi dự báo 5 giây tới, rồi từ đó sinh cảnh báo nếu cần:

```python
class RealtimePredictor:
    def __init__(self, model, scaler):
        self.model = model.eval()
        self.scaler = scaler

    def predict(self, buffer):
        if len(buffer) < 50:
            return None
        X = self.scaler.transform(np.array(buffer))
        with torch.no_grad():
            y = self.model(torch.FloatTensor(X).unsqueeze(0)).numpy()[0]
        return self.scaler.inverse_transform(y)

def make_alert(prediction):
    util = prediction[:, IDX_UTIL]          # dự báo hiệu suất kênh
    for step, u in enumerate(util):
        if u > 0.95:
            eta = step * 0.1                # thời điểm dự kiến quá tải
            return ('CRITICAL', f'Kênh sắp bão hòa sau {eta:.1f}s')
    return None
```

Yêu cầu về hiệu năng là thời gian suy luận phải đủ nhỏ (dưới 100 ms) để đáp ứng thời gian thực. Mô hình LSTM với kích thước vừa phải đáp ứng tốt yêu cầu này. Kết quả định lượng về độ chính xác của mô hình và hiệu quả cảnh báo được trình bày ở Chương 7.
