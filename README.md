# HỆ THỐNG QUẢN LÝ THÚ CƯNG VÀ LỊCH CHĂM SÓC CÓ TÍCH HỢP AI (PETCARE SPA)
**Nhóm thực hiện: Nhóm 06**
* **Hà Thị Mỹ Bình** - Product Owner (PO) kiêm Lead Backend Developer
* **Nguyễn Thị Giang** - Scrum Master (SM) kiêm Frontend Developer & Tester

Công nghệ: FastAPI + SQLAlchemy (SQLite) · HTML/JS + Tailwind · AI Engine: **Google Gemini**.

---

## 1. Cấu trúc dự án
```text
PetCare_Nhom6/
├── backend/
│   ├── db_tools.py               # sao lưu / khôi phục CSDL
│   ├── app/
│   │   ├── routers/              # auth, owners, pets, services, appointments, care_records,
│   │   │                         # vaccinations, invoices, analytics, ai
│   │   ├── services/
│   │   │   ├── collision_service.py   # chống trùng lịch groomer
│   │   │   ├── ai_service.py          # Gemini client + guardrail + retry/ngắt mạch/cache
│   │   │   └── rate_limit.py          # giới hạn tần suất (đăng nhập, AI)
│   │   ├── config.py             # nạp file .env
│   │   ├── auth.py  database.py  models.py  schemas.py  main.py
│   ├── tests/                    # pytest: lịch hẹn, hóa đơn, hồ sơ, AI
│   ├── seed_data.py  requirements.txt  pytest.ini
├── frontend/                     # SPA (index.html + js/app.js), có tab "Trợ Lý AI"
├── Dockerfile  docker-compose.yml  docker-entrypoint.sh  DEPLOY.md
├── .env.example  .gitignore  run_app.py  run.bat
└── KICH_BAN_DEMO.md             # kịch bản demo
```

## 2. Chức năng
**Quản lý:** đăng nhập JWT + phân quyền (ADMIN / RECEPTIONIST / GROOMER) · CRUD chủ nuôi, thú cưng, dịch vụ ·
**gói dịch vụ** (combo, tự tính giá lẻ và mức tiết kiệm) · đặt/đổi/hủy lịch có chống trùng lịch (409) ·
hồ sơ chăm sóc (thêm/sửa/xóa) · nhắc tiêm phòng · **hóa đơn, thu tiền nhiều lần, theo dõi công nợ** ·
dashboard (doanh thu đã thu, công nợ, lượt theo dịch vụ, doanh thu theo tháng, tỷ lệ khách quay lại).

| Nhóm | Endpoint chính |
|---|---|
| Gói dịch vụ | `GET/POST /api/packages`, `GET/PUT/DELETE /api/packages/{id}` (ghi: ADMIN) |
| Hóa đơn | `POST /api/invoices` (có `paid_amount`), `POST /api/invoices/{id}/payments`, `POST /api/invoices/{id}/cancel` (ADMIN) |
| Hồ sơ chăm sóc | `PUT /api/care-records/{id}`, `DELETE /api/care-records/{id}` (ADMIN) |
| Thống kê | `GET /api/analytics/dashboard`, `/services`, `/revenue?period=month\|day` |

Trạng thái hóa đơn: `PAID` (đã thu đủ) · `PARTIAL` (còn nợ) · `UNPAID` (chưa thu) · `CANCELLED` (không tính doanh thu/công nợ). Hóa đơn có số tiền phải thu lớn hơn 0 mặc định là chưa thu; dùng nút **Thu tiền** để xác nhận thanh toán, hoặc nhập số tiền khách thực trả ngay khi lập. Hóa đơn bằng 0 đồng không còn số tiền phải thu.

Lịch đang chờ có nút **Hoàn tất**; cả ba vai trò có thể xác nhận sau khi dịch vụ được thực hiện. Lịch đã hủy hoặc đã hoàn tất không thể xác nhận lại. Hệ thống chưa giới hạn lịch theo từng nhân viên.

**AI (Gemini):**
| Chức năng | Endpoint | Mô tả |
|---|---|---|
| Nhắc lịch | `POST /api/ai/reminder` | Soạn tin nhắn nhắc lịch spa hoặc lịch tiêm nhắc lại cho chủ nuôi |
| Tóm tắt hồ sơ | `POST /api/ai/summary/{pet_id}` | Tóm tắt hồ sơ chăm sóc gần đây của thú cưng |
| Hỏi đáp | `POST /api/ai/ask` | Trả lời câu hỏi chăm sóc cơ bản, kèm cảnh báo hỏi bác sĩ thú y |
| Trạng thái | `GET /api/ai/status` | Cho biết đã cấu hình Gemini chưa |

### An toàn khi dùng AI
1. **Cảnh báo cố định** "AI không thay thế bác sĩ thú y" được gắn từ phía code ở mọi phản hồi và hiển thị trên giao diện.
2. **Lọc đầu vào (không gọi AI):** câu hỏi có dấu hiệu khẩn cấp (co giật, khó thở, nôn ra máu, ăn nhầm socola...) →
   trả lời cố định, khuyên gặp bác sĩ thú y ngay. Câu hỏi xin chẩn đoán / kê đơn / liều thuốc → từ chối.
   Câu cố tình vượt rào (prompt injection) → từ chối.
3. **System prompt** giới hạn phạm vi; dữ liệu người dùng bọc trong thẻ `<du_lieu>`, `<cau_hoi>` và được coi là dữ liệu, không phải chỉ thị.
4. **Lọc đầu ra:** nếu AI lỡ nêu liều thuốc / kê đơn, câu trả lời bị thay bằng lời từ chối.
5. **Quyền riêng tư:** chỉ gửi tên chủ nuôi, thông tin thú cưng và hồ sơ chăm sóc; **không gửi** số điện thoại, địa chỉ, email.
6. **Dự phòng:** chưa có API key hoặc Gemini lỗi → hệ thống dùng mẫu tin nhắn/tóm tắt cố định, không bị sập.

### Phân quyền theo vai trò

| Chức năng | Quản trị (ADMIN) | Lễ tân (RECEPTIONIST) | Chăm sóc (GROOMER) |
|---|---|---|---|
| Khách hàng, thú cưng | Xem, thêm, sửa, xóa | Xem, thêm, sửa | Xem; thông tin liên hệ được che |
| Dịch vụ và gói | Xem, thêm, sửa, xóa | Xem | Xem |
| Lịch hẹn | Xem, đặt, đổi, hủy, hoàn tất | Xem, đặt, đổi, hủy, hoàn tất | Xem, hoàn tất |
| Hồ sơ chăm sóc | Xem, thêm, sửa, xóa | Xem, thêm, sửa | Xem, thêm, sửa |
| Lịch tiêm nhắc | Xem, thêm, sửa, xóa | Xem, thêm, sửa, đánh dấu hoàn thành | Xem |
| Hóa đơn và thanh toán | Xem, lập, thu tiền, hủy | Xem, lập, thu tiền | Không truy cập |
| Thống kê | Xem | Xem | Không truy cập |
| Trợ lý AI | Dùng và xem nhật ký | Dùng | Dùng |

Quyền được kiểm tra tại API theo vai trò tài khoản trong CSDL; ẩn nút chỉ để giao diện dễ sử dụng. Nhân viên chăm sóc hiện thấy lịch và hồ sơ của tất cả thú cưng, chưa có phân công theo từng nhân viên. Tài khoản mẫu chỉ dùng để demo.

## 3. Cài đặt và chạy
```bash
pip install -r backend/requirements.txt          # chạy test thì dùng requirements-dev.txt
cp .env.example .env            # Windows: copy .env.example .env
# mở .env, điền GEMINI_API_KEY (lấy tại https://aistudio.google.com/apikey) và đặt SECRET_KEY riêng
python backend/seed_data.py     # CHỈ dùng cho demo: xóa toàn bộ dữ liệu hiện có
python run_app.py               # hoặc double-click run.bat trên Windows
```
* Giao diện: http://127.0.0.1:8000/app/index.html · Swagger: http://127.0.0.1:8000/docs
* Lệnh `seed_data.py` xóa toàn bộ bảng và dữ liệu hiện có. Chỉ chạy trên CSDL demo mới, không chạy trên dữ liệu thực.
* Đổi `SECRET_KEY` và tài khoản demo trước khi triển khai; tài khoản demo không phù hợp cho môi trường thực.
* Nếu **không** điền `GEMINI_API_KEY`, ứng dụng vẫn chạy ở chế độ dự phòng; các bài test sử dụng Gemini giả lập.

**Tài khoản demo:** `admin/admin123` · `letan/letan123` · `groomer/groomer123`

### Cấu hình Gemini trên Windows

Chạy `cai_dat_gemini.bat`, dán khóa sau `GEMINI_API_KEY=` trong Notepad, lưu và đóng. Khởi động lại bằng `run.bat`. Tệp cấu hình sẵn có được giữ nguyên. `run.bat` không tự nạp lại dữ liệu mẫu; chỉ chạy `seed_data.py` khi muốn xóa dữ liệu cũ để tạo demo.

## 4. Kiểm thử

Dự án sử dụng **pytest** để kiểm tra nghiệp vụ, phân quyền, cơ sở dữ liệu và chức năng AI. Các bài test API dùng FastAPI TestClient và CSDL SQLite thử nghiệm; Gemini được **giả lập**, không gửi câu hỏi tới Gemini thật và không cần API key. Bộ lọc an toàn, tình huống Gemini lỗi và nội dung dự phòng cũng được kiểm tra.

### 4.1. Cài đặt và chạy toàn bộ test trên Windows

Mở CMD trong thư mục gốc dự án (cùng thư mục với `run.bat`) và chạy:

```bat
python -m pip install -r backend\requirements-dev.txt
cd backend
set "DATABASE_PATH=%TEMP%\petcare-pytest.db"
python -m pytest -o addopts= -q
```

Biến `DATABASE_PATH` ở trên đưa CSDL khởi tạo khi chạy test vào thư mục tạm, tránh dùng `petcare.db` của ứng dụng. Sau khi chạy xong, đóng cửa sổ CMD này hoặc gõ `set "DATABASE_PATH="` trước khi dùng lại cửa sổ để chạy ứng dụng. Không cần chạy `seed_data.py` để chạy test.

Trên macOS/Linux, từ thư mục gốc dự án:

```bash
python3 -m pip install -r backend/requirements-dev.txt
cd backend
DATABASE_PATH=/tmp/petcare-pytest.db python3 -m pytest -o addopts= -q
```

### 4.2. Chạy một nhóm test

Sau khi vào thư mục `backend` và đặt `DATABASE_PATH` như trên, có thể chạy riêng:

```bat
python -m pytest -o addopts= -q tests/test_appointments.py
python -m pytest -o addopts= -q tests/test_invoices.py
python -m pytest -o addopts= -q tests/test_care_records.py
python -m pytest -o addopts= -q tests/test_ai_service.py tests/test_ai_api.py
python -m pytest -o addopts= -q tests/test_role_permissions.py
```

### 4.3. Nội dung kiểm thử

| Tệp | Trường hợp | Nội dung chính |
|---|---:|---|
| `test_appointments.py` | 13 | Đặt, đổi, hủy và hoàn tất lịch; trùng lịch, lịch liền kề, dữ liệu sai và phân quyền. |
| `test_invoices.py` | 18 | Tính tiền, giảm giá, hóa đơn chưa thu, thu một phần/nhiều lần, thu đủ, công nợ, hủy và doanh thu. |
| `test_care_records.py` | 10 | Thêm, xem, sửa, xóa hồ sơ; kiểm tra lịch sai thú cưng, không tồn tại hoặc đã hủy. |
| `test_crud_management.py` | 2 | Thêm, sửa, xóa lịch nhắc tiêm; kiểm tra quyền và thay đổi chủ nuôi của thú cưng. |
| `test_packages.py` | 6 | Gói dịch vụ, tính giá và phân quyền. |
| `test_ai_service.py` | 24 | Prompt, câu hỏi chăm sóc và câu hỏi nguy hiểm, lọc đầu ra, dữ liệu gửi AI và nội dung dự phòng. |
| `test_ai_api.py` | 15 | API nhắc lịch, tóm tắt hồ sơ, hỏi đáp, xác thực và kiểm tra dữ liệu. |
| `test_resilience.py` | 8 | Thử lại, ngắt mạch, cache và xử lý khi Gemini không khả dụng. |
| `test_role_permissions.py` | 21 | Kiểm tra quyền cho quản lý, lễ tân và nhân viên chăm sóc khi gọi API. |
| `test_security.py` | 13 | Đăng nhập, JWT, che thông tin chủ nuôi, giới hạn tần suất và ràng buộc dữ liệu. |
| `test_db_tools.py` | 6 | Sao lưu, kiểm tra và khôi phục CSDL. |
| **Tổng** | **136** | Số trường hợp pytest thu thập được trong bản hiện tại; gồm các trường hợp tham số hóa. |

Kết quả kiểm tra ngày 30/10/2026 trên Python 3.12: **136 passed**, có 757 cảnh báo thư viện; không có test thất bại.

Bộ câu hỏi AI có 41 câu: 14 câu khẩn cấp, 12 câu yêu cầu chẩn đoán/kê đơn, 5 câu vượt rào và 10 câu chăm sóc thông thường. Test kiểm tra hành vi đối với bộ câu hỏi này; không chứng minh AI an toàn trong mọi tình huống.

Khi chạy test, xem dòng cuối của pytest: `passed` là số test đạt; `failed`, `error` hoặc `skipped` cần được phân biệt. Lệnh có mã thoát khác 0 là chưa đạt. Test tự động giả lập Gemini, vì vậy cần thử riêng bằng API key và mạng thực tế nếu muốn xác minh kết nối Gemini.

## 5. Docker, sao lưu, tài liệu
* Docker: `docker compose up --build` (xem **DEPLOY.md**: biến môi trường, sao lưu/khôi phục, checklist triển khai, xử lý sự cố).
* Sao lưu/khôi phục CSDL: `python backend/db_tools.py backup | list | verify | restore <file> --yes`.
* Bảo mật & ổn định: khóa đăng nhập sau 5 lần sai, giới hạn 20 lượt AI/phút/người, thử lại + ngắt mạch + cache cho Gemini, che SĐT/địa chỉ với vai trò GROOMER, nhật ký AI không lưu nội dung, `/api/health`.
* Tài liệu demo: `KICH_BAN_DEMO.md`. Các báo cáo và hình minh họa không có trong bản đóng gói này.

## 6. Lưu ý khi nộp / dùng Git
* Không commit `.env` và `petcare.db` (đã có trong `.gitignore`). Tạo lại CSDL bằng `seed_data.py`.
* Không dán API key vào mã nguồn, báo cáo hay ảnh chụp màn hình.


## 7. Cập nhật khi đã có dữ liệu

Bản nộp không chứa `.env`, khóa API hay `petcare.db`. Nếu bạn đã có dữ liệu thực hoặc dữ liệu demo trên máy, hãy sao lưu tệp `.env` và `petcare.db` ở thư mục cũ trước khi cập nhật. Sao chép hai tệp này vào thư mục dự án mới trên máy cá nhân, không gửi chúng cùng bản nộp. **Không chạy `seed_data.py` nếu muốn giữ dữ liệu hiện có** vì lệnh này xóa dữ liệu cũ. Với bản cài đặt mới, chạy lệnh seed một lần để tạo tài khoản và dữ liệu mẫu.

Các câu trả lời AI chỉ mang tính tham khảo; kiểm thử tự động giả lập Gemini, không chứng minh dịch vụ ngoài luôn hoạt động. Tránh nhập dữ liệu cá nhân nhạy cảm trong câu hỏi và ghi chú gửi AI.
