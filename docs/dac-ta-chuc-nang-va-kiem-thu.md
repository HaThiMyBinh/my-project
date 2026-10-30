# Đặc tả chức năng PetCare để xây dựng test case

Tài liệu mô tả các chức năng và hành vi kiểm thử dựa trên phiên bản mã nguồn hiện tại. Đối chiếu `backend/app/schemas.py`, các router và `backend/tests/` khi tạo hoặc cập nhật test. Các ví dụ dưới đây là **trường hợp cần kiểm tra**, không khẳng định tất cả đã được chạy thành công. Hành vi mong muốn chưa được mã nguồn bảo đảm phải ghi là đề xuất hoặc lỗi cần xác minh, không tự suy đoán kết quả.

## 1. Nguyên tắc chung

- Vai trò: quản lý `ADMIN`, lễ tân `RECEPTIONIST`, nhân viên chăm sóc `GROOMER`. Ma trận quyền đầy đủ trong `docs/dac-ta-he-thong.md`.
- Với API có bảo vệ: kiểm thử không đăng nhập, đăng nhập đúng quyền và đăng nhập sai quyền; không coi việc ẩn nút là kiểm tra phân quyền.
- Với thao tác ghi: kiểm tra kết quả trả về **và** dữ liệu được lưu; với thao tác bị từ chối, kiểm tra dữ liệu không bị thay đổi.
- Dùng database thử nghiệm riêng và dữ liệu mẫu giả. Không chạy test hoặc `seed_data.py` trên database có dữ liệu cần giữ.
- Các mã HTTP dưới đây áp dụng cho API; kiểm thử giao diện cần kiểm tra thêm nội dung hiển thị và phản hồi thao tác.

## 2. Đăng nhập

**Đầu vào:** tên đăng nhập và mật khẩu. **Đầu ra:** token, vai trò và thông tin tài khoản khi xác thực thành công.

| Tình huống | Kết quả mong đợi |
|---|---|
| Tài khoản và mật khẩu đúng | Đăng nhập thành công, nhận token và đúng vai trò. |
| Sai mật khẩu hoặc tài khoản không tồn tại | API trả 401, không cấp token. |
| Thiếu trường bắt buộc | API trả 422. |
| Sai liên tiếp theo cùng tài khoản và IP | Mặc định sau 5 lần sai, lần thử tiếp theo trong khoảng giới hạn bị 429; giới hạn có thể cấu hình. |

## 3. Chủ nuôi và thú cưng

**Đầu vào chủ nuôi:** họ tên, số điện thoại; địa chỉ và email có thể bỏ trống. **Đầu vào thú cưng:** mã chủ nuôi, tên, loài, giống, tuổi, cân nặng và ghi chú; tuổi và một số thông tin có thể bỏ trống. **Đầu ra:** bản ghi hoặc danh sách đã cập nhật.

| Tình huống | Kết quả mong đợi |
|---|---|
| Quản lý hoặc lễ tân thêm chủ nuôi hợp lệ | Trả 201 và lưu thông tin. |
| Thêm chủ nuôi với số điện thoại đã đăng ký | Trả 400. |
| Thêm thú cưng với chủ nuôi không tồn tại | Trả 404. |
| Tuổi thú cưng nhỏ hơn 0 hoặc lớn hơn 40; cân nặng không lớn hơn 0 hoặc lớn hơn 150 | Trả 422. Kiểm tra thêm giá trị biên 0 và 40 cho tuổi, 150 cho cân nặng. |
| Lễ tân thử xóa, nhân viên chăm sóc thử thêm/sửa/xóa | Bị từ chối theo quyền; dữ liệu không đổi. |
| Nhân viên chăm sóc xem chủ nuôi | Số điện thoại được che, địa chỉ và email không được tiết lộ. |

## 4. Dịch vụ và gói dịch vụ

**Đầu vào dịch vụ:** tên, thời lượng, giá và mô tả. **Đầu vào gói:** tên, giá, trạng thái và danh sách dịch vụ với số lượng. **Đầu ra:** thông tin dịch vụ hoặc gói được lưu và hiển thị.

| Tình huống | Kết quả mong đợi |
|---|---|
| Quản lý tạo dịch vụ, tạo gói với dữ liệu hợp lệ | Trả 201 và lưu đúng thông tin. |
| Lễ tân hoặc nhân viên chăm sóc thử ghi dữ liệu dịch vụ/gói | Bị từ chối theo quyền. |
| Gói không có dịch vụ, số lượng dưới 1, giá âm hoặc tên ngắn hơn 2 ký tự | Trả 422. |
| Dịch vụ xuất hiện hai lần trong gói | Trả 422; sử dụng số lượng để thể hiện nhiều lần. |
| Gói tham chiếu dịch vụ không tồn tại | Trả 404. |
| Xóa dịch vụ đang thuộc một gói | Trả 409. |

## 5. Lịch hẹn

**Đầu vào:** thú cưng, dịch vụ, tên thợ, ngày `YYYY-MM-DD`, giờ bắt đầu và kết thúc `HH:MM`, ghi chú. **Đầu ra:** lịch hẹn và trạng thái tương ứng.

| Tình huống | Kết quả mong đợi |
|---|---|
| Tạo lịch hợp lệ, thợ chưa bận | Trả 201 và lưu lịch. |
| Cùng thợ, cùng ngày, khung giờ giao nhau | Trả 409 và không tạo lịch. |
| Cùng thợ, giờ bắt đầu lịch mới bằng giờ kết thúc lịch cũ | Không xem là giao nhau; có thể tạo nếu dữ liệu khác hợp lệ. |
| Thú cưng hoặc dịch vụ không tồn tại | Trả 404. |
| Ngày/giờ sai định dạng, hoặc giờ kết thúc không sau giờ bắt đầu | Trả 422. |
| Đổi lịch sang thời gian trùng | Trả 409; lịch cũ không đổi. |
| Quản lý, lễ tân hoặc nhân viên chăm sóc hoàn tất lịch đang chờ | Lịch chuyển sang `COMPLETED`. |
| Hoàn tất lịch đã hủy hoặc đã hoàn tất | Trả 409. |
| Nhân viên chăm sóc thử đặt, đổi hoặc hủy lịch | Bị từ chối theo quyền. |

## 6. Hồ sơ chăm sóc

**Đầu vào:** thú cưng, lịch hẹn nếu có, cân nặng sau chăm sóc, tình trạng da, hành vi và lời khuyên. **Đầu ra:** hồ sơ được lưu theo thú cưng.

| Tình huống | Kết quả mong đợi |
|---|---|
| Tạo hồ sơ hợp lệ, có hoặc không gắn lịch hẹn | Trả 201 và lưu hồ sơ. |
| Thú cưng hoặc lịch hẹn được chọn không tồn tại | Trả 404. |
| Lịch hẹn thuộc thú cưng khác | Trả 422. |
| Lịch hẹn đã hủy | Trả 409 khi tạo hồ sơ gắn lịch. |
| Lễ tân hoặc nhân viên chăm sóc thử xóa hồ sơ | Bị từ chối; quản lý có quyền xóa. |

## 7. Nhắc tiêm phòng

**Đầu vào:** thú cưng, tên vaccine, ngày tiêm trước nếu có, ngày nhắc tiếp theo và trạng thái. **Đầu ra:** lịch nhắc thông tin, không phải chỉ định y tế.

| Tình huống | Kết quả mong đợi |
|---|---|
| Quản lý hoặc lễ tân tạo lịch nhắc hợp lệ | Trả 201 và lưu thông tin. |
| Tạo lịch với thú cưng không tồn tại | Trả 404. |
| Quản lý hoặc lễ tân đánh dấu hoàn thành | Trạng thái lịch được cập nhật. |
| Nhân viên chăm sóc thử tạo, sửa hoặc xóa | Bị từ chối theo quyền. |

## 8. Hóa đơn và thanh toán

**Đầu vào:** chủ nuôi, lịch hẹn nếu có, danh sách dịch vụ/số lượng, giảm giá, số tiền đã trả nếu có và phương thức thanh toán. **Đầu ra:** tổng tiền, tiền phải thu, đã thu, còn nợ và trạng thái.

| Tình huống | Kết quả mong đợi |
|---|---|
| Lập hóa đơn 150.000 đồng, không nhập tiền đã trả | Chưa thu (`UNPAID`), đã thu 0, còn nợ 150.000 đồng. |
| Thu 50.000 đồng cho hóa đơn trên | Thu một phần (`PARTIAL`), còn nợ 100.000 đồng. |
| Thu tiếp 100.000 đồng | Đã thu đủ (`PAID`), còn nợ 0. |
| Thu vượt số tiền còn nợ | Trả 422, không ghi nhận khoản thu. |
| Thu tiền cho hóa đơn đã hủy hoặc đã thu đủ | Trả 409. |
| Không có dòng dịch vụ hoặc số lượng nhỏ hơn 1 | Trả 422. |
| Chủ nuôi, lịch hẹn hoặc dịch vụ được chỉ định không tồn tại | Trả 404. |
| Lễ tân hoặc nhân viên chăm sóc thử hủy hóa đơn | Bị từ chối; chỉ quản lý có quyền hủy. |
| Nhân viên chăm sóc thử truy cập hóa đơn | Bị từ chối theo quyền. |

## 9. Thống kê

**Đầu vào:** dữ liệu lịch hẹn, hóa đơn và thanh toán; bộ lọc thời gian nếu có. **Đầu ra:** các chỉ số và danh sách thống kê.

| Tình huống | Kết quả mong đợi |
|---|---|
| Quản lý hoặc lễ tân xem dashboard | Có thể xem theo quyền. |
| Nhân viên chăm sóc truy cập thống kê | Bị từ chối theo quyền. |
| Có hóa đơn đã hủy | Không tính hóa đơn đã hủy vào doanh thu/công nợ; dùng dữ liệu thử nghiệm để đối chiếu. |
| Lọc thống kê theo khoảng thời gian | Kết quả chỉ phản ánh dữ liệu phù hợp bộ lọc được API hỗ trợ. |

Quyền các endpoint thống kê chi tiết có thể khác dashboard; kiểm tra router trước khi đặt kết quả mong đợi cho từng endpoint.

## 10. Chức năng AI

**Đầu vào:** lịch hẹn hoặc lịch tiêm của thú cưng, hồ sơ chăm sóc, hoặc câu hỏi từ người dùng. **Đầu ra:** nội dung tham khảo, cảnh báo thú y và thông tin nguồn phản hồi.

| Tình huống | Kết quả mong đợi |
|---|---|
| Yêu cầu nhắc lịch cho thú cưng có lịch phù hợp | Trả bản nháp liên quan đến lịch; nhân viên tự kiểm tra và gửi. |
| Yêu cầu nhắc nhưng không có lịch phù hợp hoặc thú cưng không tồn tại | API trả 404. |
| Tóm tắt hồ sơ thú cưng | Có nội dung tóm tắt hoặc dự phòng phù hợp dữ liệu hiện có và cảnh báo tham khảo. |
| Câu hỏi thông thường hợp lệ | Trả câu trả lời tham khảo và cảnh báo; không yêu cầu câu chữ AI cố định. |
| Câu hỏi ngắn dưới 3 ký tự sau khi bỏ khoảng trắng, hoặc dài hơn 500 ký tự | Trả 422. |
| Câu hỏi có dấu hiệu khẩn cấp, yêu cầu chẩn đoán/kê đơn, hoặc cố vượt rào | Kiểm tra guardrail phù hợp; không cung cấp chẩn đoán, liều thuốc; tình huống khẩn cấp khuyên gặp bác sĩ thú y. |
| Chưa cấu hình Gemini hoặc dịch vụ lỗi | Kiểm tra phản hồi dự phòng và thông tin nguồn; không làm sập ứng dụng. |
| Gọi AI quá nhanh | Có thể bị giới hạn và trả 429. |

Khi test tự động, giả lập Gemini để kết quả ổn định và tránh cần khóa API. Nếu cần chứng minh kết nối thật, kiểm thử riêng với khóa cấu hình an toàn và ghi nhận kết quả thực tế. Nội dung người dùng nhập tự do có thể chứa thông tin cá nhân, không dùng dữ liệu nhạy cảm trong test.

## 11. Mẫu yêu cầu AI sinh test case

> Đọc `docs/dac-ta-chuc-nang-va-kiem-thu.md`, `docs/dac-ta-he-thong.md` và mã nguồn liên quan. Hãy tạo bảng test case cho chức năng [tên chức năng], gồm: mã test, mục tiêu, điều kiện trước, dữ liệu đầu vào, các bước, kết quả mong đợi và mức ưu tiên. Bao gồm trường hợp hợp lệ, không hợp lệ, giá trị biên và phân quyền. Phân biệt hành vi đã có trong code với đề xuất cần xác minh; không tự ghi test đã pass khi chưa chạy.

Ví dụ: thay `[tên chức năng]` bằng **lịch hẹn**, **hóa đơn**, **hồ sơ chăm sóc** hoặc **trợ lý AI**. Hướng dẫn chạy test có trong `README.md`.
