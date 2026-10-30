# Tổng quan mã nguồn PetCare

Tài liệu này giúp thành viên nhóm và công cụ hỗ trợ lập trình tìm nhanh phần mã liên quan khi đọc, sửa và kiểm thử dự án. Nội dung mô tả cấu trúc hiện tại; khi sửa, cần đối chiếu trực tiếp mã nguồn và yêu cầu mới nhất.

## 1. Công nghệ và cách hoạt động

- **Backend:** Python, FastAPI và SQLAlchemy.
- **Frontend:** HTML, JavaScript và Tailwind; FastAPI phục vụ giao diện tại `/app/index.html`.
- **Cơ sở dữ liệu:** SQLite; mặc định là `petcare.db` tại thư mục gốc, có thể đổi bằng `DATABASE_PATH`.
- **AI:** Google Gemini; có guardrail và nội dung dự phòng khi AI không sẵn sàng.
- **Kiểm thử:** pytest, FastAPI TestClient và cơ sở dữ liệu thử nghiệm; các test Gemini sử dụng giả lập.

## 2. Các thư mục và file chính

```text
my-project/
├── codebase.md                 Tổng quan mã nguồn
├── README.md                   Cài đặt, chạy và kiểm thử
├── .env.example                Mẫu cấu hình môi trường
├── run.bat, run_app.py         Khởi động ứng dụng
├── backend/
│   ├── app/
│   │   ├── main.py             Tạo ứng dụng, đăng ký API, phục vụ frontend
│   │   ├── config.py           Đọc cấu hình môi trường
│   │   ├── database.py         Kết nối SQLite và phiên làm việc
│   │   ├── models.py           Mô hình và quan hệ dữ liệu
│   │   ├── schemas.py          Định dạng và kiểm tra dữ liệu API
│   │   ├── auth.py             Token, xác thực và phân quyền
│   │   ├── routers/            Endpoint theo từng chức năng
│   │   └── services/           Nghiệp vụ AI, chống trùng lịch, giới hạn tần suất
│   ├── tests/                  Kiểm thử pytest
│   ├── db_tools.py             Công cụ sao lưu, khôi phục database
│   ├── seed_data.py            Tạo dữ liệu mẫu; có thể xóa dữ liệu hiện có
│   ├── requirements.txt        Thư viện chạy ứng dụng
│   └── requirements-dev.txt    Thư viện phục vụ phát triển và test
├── frontend/
│   ├── index.html              Giao diện chính
│   └── js/app.js               Xử lý giao diện và gọi API
├── docs/                       Đặc tả chức năng và tài liệu kiểm thử
└── reports/                    Báo cáo kỹ thuật
```

Giao diện có thể dùng lớp Tailwind trong HTML thay vì một file CSS riêng. Kiểm tra `frontend/index.html` và `frontend/js/app.js` khi sửa giao diện.

## 3. Tìm mã theo chức năng

| Chức năng | Backend | Frontend và kiểm thử liên quan |
|---|---|---|
| Đăng nhập, quyền | `routers/auth.py`, `auth.py`, `services/rate_limit.py` | `frontend/js/app.js`; `test_security.py`, `test_role_permissions.py` |
| Chủ nuôi, thú cưng | `routers/owners.py`, `routers/pets.py`, `models.py`, `schemas.py` | `frontend/js/app.js`; `test_crud_management.py`, `test_role_permissions.py` |
| Dịch vụ, gói | `routers/services.py`, `routers/packages.py` | `frontend/js/app.js`; `test_packages.py`, `test_role_permissions.py` |
| Lịch hẹn | `routers/appointments.py`, `services/collision_service.py` | `frontend/js/app.js`; `test_appointments.py` |
| Hồ sơ chăm sóc | `routers/care_records.py` | `frontend/js/app.js`; `test_care_records.py` |
| Nhắc tiêm phòng | `routers/vaccinations.py` | `frontend/js/app.js`; kiểm tra thêm test phân quyền |
| Hóa đơn, thu tiền | `routers/invoices.py` | `frontend/js/app.js`; `test_invoices.py` |
| Dashboard và thống kê | `routers/analytics.py` | `frontend/js/app.js`; kiểm tra thêm test phân quyền |
| AI | `routers/ai.py`, `services/ai_service.py`, `services/rate_limit.py` | `frontend/js/app.js`; `test_ai_api.py`, `test_ai_service.py`, `ai_cases.py`, `test_resilience.py` |
| Sao lưu và khôi phục | `backend/db_tools.py` | `test_db_tools.py` |

Các tên test trong bảng nằm trong `backend/tests/`; tên router và service nằm trong `backend/app/`.

## 4. Luồng xử lý chính

1. Người dùng thao tác trên giao diện; JavaScript gửi yêu cầu tới API FastAPI.
2. API kiểm tra dữ liệu đầu vào qua schema và xác thực, phân quyền theo tài khoản khi endpoint yêu cầu.
3. Router và service xử lý nghiệp vụ; SQLAlchemy đọc hoặc ghi SQLite.
4. API trả kết quả hoặc thông báo lỗi để giao diện hiển thị.

Với AI, router lấy dữ liệu cần thiết rồi gọi `ai_service.py`. Hệ thống kiểm tra an toàn và có thể dùng phản hồi dự phòng. Tin nhắn nhắc là bản nháp, nhân viên tự kiểm tra và gửi; hệ thống không tự gửi cho chủ nuôi.

## 5. Dữ liệu và bảo mật

- `database.py` bật kiểm tra khóa ngoại SQLite. `main.py` tạo các bảng chưa tồn tại khi khởi động; việc này không thay thế hệ thống di chuyển schema khi thay đổi cấu trúc.
- Bảng `users` hiện không được nối với bảng khác bằng khóa ngoại. `ai_logs.username` và `appointments.groomer_name` lưu dữ liệu dạng chữ.
- Không ghi API key, mật khẩu, `.env` hoặc dữ liệu thật vào Git, test hay tài liệu. Dữ liệu trong ghi chú tự do có thể chứa thông tin cá nhân; cần cân nhắc trước khi gửi cho AI.
- **Không chạy `backend/seed_data.py` trên database cần giữ:** script tạo lại dữ liệu mẫu và có thể xóa dữ liệu hiện có. Sao lưu trước khi khôi phục hoặc sửa database.
- Kiểm tra quyền tại backend; không dựa vào việc ẩn nút trên giao diện. Nhân viên chăm sóc hiện chưa bị giới hạn lịch theo từng người.

## 6. Chạy và kiểm thử

Xem `README.md` để cài đặt và chạy ứng dụng. Trên Windows, mở CMD tại thư mục gốc dự án để chạy toàn bộ test:

```bat
python -m pip install -r backend\requirements-dev.txt
cd backend
set "DATABASE_PATH=%TEMP%\petcare-pytest.db"
python -m pytest -o addopts= -q
```

Đường dẫn tạm giúp tránh dùng `petcare.db` của ứng dụng khi khởi tạo test. Sau khi chạy, đóng CMD hoặc chạy `set "DATABASE_PATH="` trước khi dùng lại cửa sổ để chạy ứng dụng. Không cần tạo dữ liệu mẫu để chạy test. Test Gemini giả lập không chứng minh kết nối Gemini thật thành công.

## 7. Tài liệu và cách giao việc cho AI

- `docs/dac-ta-chuc-nang-he-thong.md`: mục đích, người dùng, đầu vào, xử lý và đầu ra của các chức năng.
- `docs/dac-ta-chuc-nang-va-kiem-thu.md`: các trường hợp cần kiểm tra và mẫu yêu cầu sinh test case.
- `docs/dac-ta-he-thong.md`: tổng quan, phân quyền và quy tắc nghiệp vụ.
- `README.md`, `DEPLOY.md`, `KICH_BAN_DEMO.md`: hướng dẫn chạy, triển khai và trình bày.

Ví dụ yêu cầu: “Đọc `codebase.md` và đặc tả chức năng, tìm code liên quan đến lịch hẹn, sửa lỗi theo yêu cầu, giữ dữ liệu hiện có và chạy test phù hợp.” Cần kiểm tra kết quả chạy thực tế, không tự khẳng định test đã pass.
