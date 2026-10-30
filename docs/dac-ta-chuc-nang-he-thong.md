# ĐẶC TẢ CHỨC NĂNG HỆ THỐNG PETCARE

## 1. Giới thiệu

Hệ thống PetCare hỗ trợ cửa hàng dịch vụ thú cưng quản lý khách hàng, thú cưng, dịch vụ, lịch hẹn, hồ sơ chăm sóc, lịch nhắc tiêm, hóa đơn và thống kê. Trợ lý AI hỗ trợ nhân viên soạn tin nhắn nhắc lịch, tóm tắt hồ sơ và trả lời các câu hỏi chăm sóc cơ bản.

**Phạm vi người dùng:** quản lý, lễ tân và nhân viên chăm sóc đăng nhập để sử dụng hệ thống. Chủ nuôi là khách hàng được quản lý trong hệ thống; phiên bản hiện tại chưa có tài khoản hay giao diện đăng ký riêng cho chủ nuôi.

Tài liệu mô tả phiên bản hiện tại. Khi thay đổi hệ thống, cần đối chiếu mã nguồn và cập nhật đặc tả tương ứng.

## 2. Người dùng và phân quyền

| Chức năng | Quản lý | Lễ tân | Nhân viên chăm sóc |
|---|---|---|---|
| Chủ nuôi và thú cưng | Xem, thêm, sửa, xóa | Xem, thêm, sửa | Xem; thông tin liên hệ được che |
| Dịch vụ và gói dịch vụ | Xem, thêm, sửa, xóa | Xem | Xem |
| Lịch hẹn | Xem, đặt, đổi, hủy, hoàn tất | Xem, đặt, đổi, hủy, hoàn tất | Xem, hoàn tất |
| Hồ sơ chăm sóc | Xem, thêm, sửa, xóa | Xem, thêm, sửa | Xem, thêm, sửa |
| Lịch nhắc tiêm phòng | Xem, thêm, sửa, xóa, đánh dấu hoàn thành | Xem, thêm, sửa, đánh dấu hoàn thành | Xem |
| Hóa đơn và thanh toán | Xem, lập, thu tiền, hủy | Xem, lập, thu tiền | Không truy cập |
| Dashboard thống kê | Xem | Xem | Không truy cập |
| Trợ lý AI | Sử dụng; xem nhật ký AI | Sử dụng | Sử dụng |

Phân quyền được kiểm tra ở backend. Hệ thống hiện chưa giới hạn lịch và hồ sơ theo từng nhân viên phụ trách. Một số báo cáo chi tiết có thể có quyền truy cập riêng; cần đối chiếu API tương ứng.

## 3. Các chức năng

### 3.1. Đăng nhập và xác thực

- **Mục đích:** xác thực người dùng và cấp quyền theo vai trò.
- **Người dùng:** quản lý, lễ tân, nhân viên chăm sóc.
- **Đầu vào:** tên đăng nhập và mật khẩu.
- **Xử lý:** kiểm tra thông tin tài khoản; nếu hợp lệ, cấp token để sử dụng các chức năng được phép. Hệ thống giới hạn các lần đăng nhập sai theo tài khoản và địa chỉ IP.
- **Đầu ra:** đăng nhập thành công và hiển thị vai trò, hoặc thông báo lỗi khi thông tin không hợp lệ / bị giới hạn.

### 3.2. Quản lý chủ nuôi

- **Mục đích:** lưu và tra cứu thông tin khách hàng.
- **Người dùng:** quản lý, lễ tân; nhân viên chăm sóc được xem thông tin đã hạn chế.
- **Đầu vào:** họ tên, số điện thoại, địa chỉ và email nếu có.
- **Xử lý:** xem danh sách, thêm hoặc sửa chủ nuôi; quản lý có quyền xóa. Khi thêm mới, hệ thống kiểm tra số điện thoại đã được đăng ký hay chưa.
- **Đầu ra:** thông tin chủ nuôi được hiển thị và lưu trong cơ sở dữ liệu; thông báo lỗi khi thao tác không hợp lệ.

### 3.3. Quản lý thú cưng

- **Mục đích:** quản lý thông tin từng thú cưng và chủ sở hữu.
- **Người dùng:** quản lý, lễ tân; nhân viên chăm sóc được xem.
- **Đầu vào:** chủ nuôi, tên thú cưng, loài, giống, tuổi, cân nặng và ghi chú sức khỏe nếu có.
- **Xử lý:** xem, thêm, sửa thông tin; quản lý có quyền xóa. Hệ thống kiểm tra chủ nuôi tồn tại, tuổi và cân nặng nằm trong phạm vi được hỗ trợ.
- **Đầu ra:** hồ sơ thú cưng được lưu và liên kết với chủ nuôi tương ứng.

### 3.4. Quản lý dịch vụ và gói dịch vụ

- **Mục đích:** quản lý danh mục dịch vụ, bảng giá và các gói gồm nhiều dịch vụ.
- **Người dùng:** quản lý được thêm, sửa, xóa; lễ tân và nhân viên chăm sóc được xem.
- **Đầu vào:** tên dịch vụ, thời lượng, giá và mô tả; đối với gói gồm tên gói, giá, trạng thái và danh sách dịch vụ cùng số lượng.
- **Xử lý:** lưu danh mục; kiểm tra dịch vụ được chọn trong gói tồn tại và không bị lặp. Không xóa dịch vụ đang nằm trong gói khi chưa gỡ dịch vụ đó khỏi gói.
- **Đầu ra:** thông tin dịch vụ, gói dịch vụ và giá hiển thị cho nhân viên.

### 3.5. Đặt, đổi, hủy và hoàn tất lịch hẹn

- **Mục đích:** sắp xếp lịch chăm sóc cho thú cưng và hạn chế trùng lịch của thợ.
- **Người dùng:** quản lý và lễ tân được đặt, đổi, hủy, hoàn tất; nhân viên chăm sóc được xem và hoàn tất.
- **Đầu vào:** thú cưng, dịch vụ, tên thợ, ngày, giờ bắt đầu, giờ kết thúc và ghi chú.
- **Xử lý:** kiểm tra thú cưng, dịch vụ, ngày giờ và lịch của cùng thợ. Khi thời gian giao nhau, hệ thống từ chối lịch trùng. Lịch đang chờ có thể được đánh dấu hoàn tất; lịch đã hủy hoặc hoàn tất không hoàn tất lại được.
- **Đầu ra:** danh sách lịch và trạng thái; thông báo khi đặt, đổi, hủy hoặc hoàn tất. Nếu trùng lịch hoặc dữ liệu sai, hệ thống thông báo lỗi.

### 3.6. Quản lý hồ sơ chăm sóc

- **Mục đích:** ghi nhận kết quả chăm sóc và tình trạng thú cưng.
- **Người dùng:** cả ba vai trò được xem, thêm, sửa; chỉ quản lý được xóa.
- **Đầu vào:** thú cưng, lịch hẹn nếu có, cân nặng sau chăm sóc, tình trạng da, hành vi và lời khuyên.
- **Xử lý:** lưu hồ sơ cho thú cưng. Nếu gắn lịch hẹn, lịch phải thuộc đúng thú cưng; không tạo hồ sơ gắn với lịch đã hủy.
- **Đầu ra:** lịch sử chăm sóc để nhân viên tra cứu và dùng làm ngữ cảnh cho chức năng tóm tắt AI.

### 3.7. Quản lý lịch nhắc tiêm phòng

- **Mục đích:** theo dõi thông tin nhắc tiêm hoặc phòng bệnh.
- **Người dùng:** quản lý và lễ tân được xem, thêm, sửa, đánh dấu hoàn thành; quản lý được xóa; nhân viên chăm sóc được xem.
- **Đầu vào:** thú cưng, tên vaccine, ngày tiêm trước nếu có, ngày nhắc tiếp theo và trạng thái.
- **Xử lý:** lưu lịch nhắc theo thú cưng và cập nhật khi đã hoàn thành.
- **Đầu ra:** danh sách lịch nhắc và trạng thái để nhân viên theo dõi. Đây là thông tin hỗ trợ, không thay thế hướng dẫn của bác sĩ thú y.

### 3.8. Lập hóa đơn và theo dõi thanh toán

- **Mục đích:** ghi nhận chi phí dịch vụ, tiền đã thu và công nợ.
- **Người dùng:** quản lý và lễ tân được xem, lập và thu tiền; chỉ quản lý được hủy hóa đơn.
- **Đầu vào:** chủ nuôi, lịch hẹn nếu có, dịch vụ, số lượng, giảm giá, số tiền thực trả và phương thức thanh toán.
- **Xử lý:** tính tiền phải thu; lưu số tiền thanh toán thực tế. Nếu không nhập tiền đã trả khi lập hóa đơn có số tiền phải thu lớn hơn 0, hóa đơn mặc định chưa thu. Có thể ghi nhận thanh toán nhiều lần cho đến khi đủ tiền. Không thu vượt số còn nợ hoặc thu cho hóa đơn đã hủy / đã thu đủ.
- **Đầu ra:** hóa đơn với tổng tiền, giảm giá, phải thu, đã thu, còn nợ và trạng thái chưa thu, thu một phần, thu đủ hoặc đã hủy. Hệ thống ghi nhận thanh toán, không tự thực hiện giao dịch ngân hàng.

### 3.9. Thống kê

- **Mục đích:** hỗ trợ theo dõi hoạt động của cửa hàng.
- **Người dùng:** quản lý và lễ tân xem dashboard; quyền của từng báo cáo chi tiết được kiểm tra tại API.
- **Đầu vào:** dữ liệu lịch hẹn, hóa đơn, thanh toán và bộ lọc được hỗ trợ.
- **Xử lý:** tổng hợp các chỉ số như lượt dịch vụ, doanh thu đã thu, công nợ và khách quay lại. Hóa đơn đã hủy không tính vào doanh thu và công nợ.
- **Đầu ra:** dashboard và báo cáo thống kê tương ứng.

### 3.10. AI soạn tin nhắn nhắc lịch

- **Mục đích:** hỗ trợ nhân viên soạn lời nhắc lịch chăm sóc hoặc lịch tiêm nhắc.
- **Người dùng:** cả ba vai trò đã đăng nhập.
- **Đầu vào:** thú cưng và loại lịch; lịch hẹn hoặc lịch nhắc phù hợp.
- **Xử lý:** lấy dữ liệu lịch liên quan và yêu cầu Gemini tạo nội dung; nếu dịch vụ AI không sẵn sàng, hệ thống sử dụng nội dung dự phòng. Khi không có lịch phù hợp, hệ thống thông báo.
- **Đầu ra:** bản nháp tin nhắn để nhân viên kiểm tra, sao chép và tự gửi cho chủ nuôi. Hệ thống không tự gửi tin nhắn.

### 3.11. AI tóm tắt hồ sơ chăm sóc

- **Mục đích:** giúp nhân viên nắm nhanh lịch sử chăm sóc của thú cưng.
- **Người dùng:** cả ba vai trò đã đăng nhập.
- **Đầu vào:** thú cưng và dữ liệu hồ sơ chăm sóc liên quan.
- **Xử lý:** tổng hợp ngữ cảnh và yêu cầu Gemini tóm tắt; có phản hồi dự phòng khi AI không sẵn sàng.
- **Đầu ra:** bản tóm tắt tham khảo kèm cảnh báo nội dung AI không thay thế bác sĩ thú y.

### 3.12. AI hỏi đáp chăm sóc cơ bản

- **Mục đích:** cung cấp thông tin tham khảo về chăm sóc thú cưng thông thường.
- **Người dùng:** cả ba vai trò đã đăng nhập.
- **Đầu vào:** câu hỏi và thú cưng nếu được chọn; câu hỏi tối đa 500 ký tự và có ít nhất 3 ký tự sau khi bỏ khoảng trắng hai đầu.
- **Xử lý:** kiểm tra câu hỏi, áp dụng bộ lọc an toàn và gửi yêu cầu tới Gemini khi phù hợp. Câu hỏi khẩn cấp hoặc yêu cầu chẩn đoán, kê đơn được xử lý theo quy tắc an toàn; có phản hồi dự phòng khi AI lỗi hoặc chưa cấu hình.
- **Đầu ra:** câu trả lời tham khảo và cảnh báo; khi có dấu hiệu bất thường hoặc khẩn cấp, khuyên liên hệ bác sĩ thú y.

## 4. Yêu cầu chung và giới hạn

- Bảo vệ tài khoản và kiểm tra quyền ở backend; không công khai khóa API, mật khẩu hay file cấu hình bí mật.
- Hạn chế thông tin cá nhân khi gửi dữ liệu cho AI; nội dung ghi chú tự do vẫn có thể chứa dữ liệu nhạy cảm.
- Bộ lọc AI chỉ giảm rủi ro và không đảm bảo phát hiện mọi trường hợp. Nhân viên cần kiểm tra nội dung AI trước khi sử dụng.
- Dữ liệu SQLite được lưu trong file `petcare.db` theo cấu hình. Sao lưu trước khi cập nhật hoặc khôi phục; không chạy `backend/seed_data.py` trên dữ liệu cần giữ vì thao tác này có thể xóa dữ liệu cũ.
- Tài liệu kiểm thử chi tiết và các trường hợp gợi ý nằm tại `docs/dac-ta-chuc-nang-va-kiem-thu.md`. Hướng dẫn chạy và kiểm thử nằm trong `README.md`.
