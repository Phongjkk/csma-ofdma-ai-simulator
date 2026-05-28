# 8. Kết luận

## 8.1. Tóm tắt kết quả

Project đã xây dựng một hệ thống hoàn chỉnh mô phỏng cơ chế CSMA/CA và OFDMA trong mạng không dây IEEE 802.11, kết hợp giám sát và dự đoán hiệu năng bằng trí tuệ nhân tạo. Các công việc đã thực hiện gồm:

- Nghiên cứu cơ sở lý thuyết về mạng không dây, cơ chế truy cập kênh CSMA/CA và cơ chế đa truy cập OFDMA, cùng nền tảng về giám sát mạng và dự đoán chuỗi thời gian.
- Phân tích mô hình toán học Bianchi làm cơ sở kiểm chứng định lượng cho bộ mô phỏng.
- Xây dựng bộ mô phỏng dựa trên kỹ thuật mô phỏng sự kiện rời rạc, mô phỏng cơ chế CSMA/CA + OFDMA kết hợp như trong Wi-Fi 6/7 thực tế.
- Kiểm chứng tính đúng đắn của bộ mô phỏng bằng cách đối chiếu với mô hình Bianchi.
- Xây dựng hệ thống giám sát thời gian thực với cơ chế cửa sổ trượt, phát hiện bất thường và quản lý cảnh báo.
- Sinh tập dữ liệu từ bộ mô phỏng và huấn luyện mô hình LSTM dự đoán hiệu năng, cảnh báo sớm quá tải.
- Phát triển giao diện trực quan phục vụ theo dõi và trình diễn.

## 8.2. Đóng góp

- **Bộ mô phỏng mã nguồn mở bằng Python:** dễ đọc, dễ tùy biến và mở rộng hơn so với các công cụ mô phỏng truyền thống viết bằng C++, phù hợp cho mục đích học tập và nghiên cứu.
- **Kiểm chứng chặt chẽ với lý thuyết:** việc đối chiếu với mô hình Bianchi đảm bảo độ tin cậy của bộ mô phỏng, là cơ sở vững chắc cho mọi kết quả sau đó.
- **Tích hợp toàn bộ luồng xử lý:** từ mô phỏng, giám sát, sinh dữ liệu, huấn luyện AI đến trực quan hóa trong cùng một khung phần mềm — gần với mô hình một hệ thống giám sát mạng thực tế.
- **Ứng dụng AI cho dự đoán sớm:** mô hình LSTM dự đoán trước tình trạng quá tải, hỗ trợ chuyển từ vận hành bị động sang chủ động.

## 8.3. Hạn chế

Project còn một số hạn chế cần ghi nhận:

- **Về mô phỏng:** chưa mô phỏng chi tiết tầng vật lý (điều chế, mã hóa kênh, MIMO, beamforming); chưa xét tính di động của thiết bị, mạng nhiều AP hay mạng mesh; chưa triển khai các tính năng đặc trưng riêng của Wi-Fi 7 như Multi-Link Operation, Multi-RU.
- **Về dữ liệu và AI:** mô hình được huấn luyện trên dữ liệu tổng hợp từ bộ mô phỏng, chưa được kiểm chứng trên dữ liệu mạng thật; bài toán hiện giới hạn ở dự đoán (hồi quy), chưa có phân loại trạng thái mạng; chưa có cơ chế học trực tuyến (online learning) để cập nhật mô hình trong quá trình vận hành.

## 8.4. Hướng phát triển

Trên cơ sở các hạn chế trên, project có thể được mở rộng theo các hướng:

- **Mở rộng mô phỏng:** bổ sung mô hình tầng vật lý chi tiết hơn, hỗ trợ tính di động, mạng nhiều AP, và các tính năng Wi-Fi 7 (MLO, Multi-RU).
- **Cải thiện mô hình AI:** thử nghiệm các kiến trúc tiên tiến hơn như Transformer cho chuỗi thời gian; bổ sung bài toán phân loại trạng thái; áp dụng học trực tuyến để mô hình tự thích nghi.
- **Kiểm chứng với dữ liệu thật:** thu thập dữ liệu từ mạng Wi-Fi thực để kiểm chứng và tinh chỉnh mô hình, thu hẹp khoảng cách giữa mô phỏng và thực tế.
- **Tối ưu hóa thông minh:** ứng dụng học tăng cường (reinforcement learning) để AP tự động tối ưu việc lập lịch và cấp phát tài nguyên RU, hướng tới mạng tự tối ưu.
