# Đặc tả hệ thống PetCare

Tài liệu này mô tả hệ thống hiện có để thành viên nhóm và công cụ hỗ trợ lập trình như Codex hiểu bối cảnh trước khi sửa. Khi tài liệu và mã nguồn khác nhau, kiểm tra lại mã nguồn, test và yêu cầu mới nhất; không tự coi tài liệu là bằng chứng chức năng đã chạy thành công.

## 1. Mục đích và công nghệ

PetCare hỗ trợ cửa hàng quản lý chủ nuôi, thú cưng, lịch chăm sóc, nhắc tiêm phòng, hồ sơ và thanh toán. Trợ lý Gemini hỗ trợ soạn lời nhắc, tóm tắt hồ sơ và trả lời câu hỏi chăm sóc cơ bản.

- Backend: FastAPI, SQLAlchemy; cơ sở dữ liệu SQLite.
- Frontend: HTML, JavaScript và Tailwind.
- AI: Google Gemini; có nội dung dự phòng khi AI không sẵn sàng.
- Tài khoản sử dụng hệ thống là quản lý, lễ tân và nhân viên chăm sóc. Chủ nuôi là dữ liệu khách hàng, không có chức năng đăng ký tài khoản riêng trong hệ thống hiện tại.

## 2. Chức năng chính

1. Đăng nhập và phân quyền theo vai trò.
2. Quản lý chủ nuôi và thú cưng.
3. Quản lý dịch vụ, bảng giá và gói dịch vụ.
4. Đặt, đổi, hủy và hoàn tất lịch chăm sóc; kiểm tra trùng lịch thợ.
5. Ghi nhận hồ sơ chăm sóc và tình trạng thú cưng.
6. Quản lý lịch nhắc tiêm phòng ở mức thông tin.
7. Lập hóa đơn, ghi nhận thanh toán và theo dõi công nợ.
8. Thống kê dịch vụ, doanh thu và khách quay lại.
9. Hỗ trợ AI soạn lời nhắc, tóm tắt hồ sơ và trả lời câu hỏi chăm sóc.

## 3. Phân quyền hiện tại

| Chức năng | Quản lý (ADMIN) | Lễ tân (RECEPTIONIST) | Nhân viên chăm sóc (GROOMER) |
|---|---|---|---|
| Chủ nuôi, thú cưng | Xem, thêm, sửa, xóa | Xem, thêm, sửa | Xem; thông tin liên hệ được che |
| Dịch vụ, gói dịch vụ | Xem, thêm, sửa, xóa | Xem | Xem |
| Lịch hẹn | Xem, đặt, đổi, hủy, hoàn tất | Xem, đặt, đổi, hủy, hoàn tất | Xem, hoàn tất |
| Hồ sơ chăm sóc | Xem, thêm, sửa, xóa | Xem, thêm, sửa | Xem, thêm, sửa |
| Nhắc tiêm phòng | Xem, thêm, sửa, xóa, đánh dấu hoàn thành | Xem, thêm, sửa, đánh dấu hoàn thành | Xem |
| Hóa đơn, thanh toán | Xem, lập, thu tiền, hủy | Xem, lập, thu tiền | Không truy cập |
| Thống kê | Xem | Xem | Không truy cập |
| Trợ lý AI | Sử dụng, xem nhật ký AI | Sử dụng | Sử dụng |

Quyền phải được kiểm tra ở API, không chỉ ẩn nút trên giao diện. Hiện chưa giới hạn lịch hoặc hồ sơ theo từng nhân viên; nhân viên chăm sóc có thể hoàn tất lịch đang chờ mà không cần được phân công riêng.

## 4. Quy tắc nghiệp vụ đáng chú ý

- Lịch hẹn của cùng thợ không được giao nhau; lịch đang chờ mới có thể đánh dấu hoàn tất. Không hoàn tất lại lịch đã hoàn tất hoặc đã hủy.
- Hồ sơ chăm sóc gắn lịch hẹn phải thuộc cùng thú cưng và không được gắn với lịch đã hủy.
- Hóa đơn có số tiền phải thu lớn hơn 0 mặc định chưa thu nếu không nhập số tiền đã trả. Có thể thu tiền nhiều lần; trạng thái thay đổi theo số tiền thực thu. Hóa đơn 0 đồng không còn tiền phải thu. Việc tạo hóa đơn không tự gửi tiền hay thực hiện giao dịch ngân hàng.
- Tin nhắn nhắc do AI tạo là bản nháp để nhân viên xem và tự gửi, không tự động gửi cho chủ nuôi.

## 5. AI và bảo mật

- Trả lời ở mức tham khảo, không thay thế bác sĩ thú y; khi có dấu hiệu bất thường hoặc khẩn cấp, khuyên liên hệ bác sĩ thú y.
- Có kiểm tra đầu vào, đầu ra và nội dung dự phòng, nhưng các bộ lọc không đảm bảo phát hiện mọi trường hợp. Không khẳng định đã kiểm thử Gemini thật nếu chỉ chạy test giả lập.
- Hạn chế dữ liệu cá nhân gửi cho AI. Các trường liên hệ có cấu trúc không được chủ động đưa vào prompt, nhưng nội dung ghi chú tự do vẫn có thể chứa dữ liệu nhạy cảm; cần kiểm tra trước khi nhập hoặc gửi.
- Không đưa API key, mật khẩu hoặc file `.env` vào tài liệu, Git hay ảnh minh họa. Cấu hình mẫu nằm trong `.env.example`.

## 6. Dữ liệu và vị trí mã nguồn

- `backend/app/models.py`: mô hình dữ liệu; `database.py`: kết nối database.
- `backend/app/routers/`: các API; `backend/app/services/`: xử lý AI, trùng lịch và giới hạn tần suất.
- `frontend/`: giao diện và JavaScript; `backend/tests/`: kiểm thử.
- Mặc định dữ liệu SQLite được lưu trong `petcare.db` ở thư mục dự án; cấu hình có thể thay đổi đường dẫn. Cần sao lưu trước khi thao tác trên dữ liệu thật.
- Bảng `users` lưu tài khoản; bảng này hiện không có khóa ngoại nối với các bảng khác. `ai_logs.username` và `appointments.groomer_name` là thông tin dạng chữ, không phải quan hệ khóa ngoại tới `users`.
- `backend/seed_data.py` tạo lại dữ liệu mẫu và có thể xóa dữ liệu hiện có; không chạy trên database cần giữ lại.

## 7. Kiểm thử và tài liệu liên quan

Xem phần **Kiểm thử** trong `README.md` để biết cách chạy test và dùng đường dẫn database thử nghiệm riêng. Các nhóm test gồm lịch hẹn, hóa đơn, hồ sơ, AI, phân quyền và bảo mật. Test Gemini giả lập không chứng minh kết nối Gemini thật đang hoạt động.

Tài liệu liên quan: `README.md`, `DEPLOY.md`, `KICH_BAN_DEMO.md` và báo cáo trong `reports/`. Khi thay đổi chức năng hoặc quyền, cập nhật tài liệu này và test liên quan nếu cần.

## 8. Hướng dẫn khi giao việc cho Codex

Ví dụ: “Đọc `docs/dac-ta-he-thong.md` và mã nguồn liên quan, sửa chức năng đặt lịch theo đúng phân quyền, sau đó chạy test phù hợp. Giữ lại dữ liệu hiện có.”

Trước khi sửa, đối chiếu đặc tả với code và yêu cầu mới nhất. Giữ bí mật cấu hình và dữ liệu hiện có; không chạy lệnh tạo lại dữ liệu mẫu trên database của người dùng.
