# HƯỚNG DẪN TRIỂN KHAI PETCARE SPA

## 1. Chạy cục bộ (không Docker)
```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cp .env.example .env                                     # Windows: copy .env.example .env
#   điền SECRET_KEY (chuỗi ngẫu nhiên dài) và GEMINI_API_KEY
python backend/seed_data.py                              # nạp dữ liệu mẫu (XÓA dữ liệu cũ)
python run_app.py
```
Mở http://127.0.0.1:8000/app/index.html · Swagger: http://127.0.0.1:8000/docs · Kiểm tra sống: `/api/health`

Tạo `SECRET_KEY` ngẫu nhiên: `python -c "import secrets; print(secrets.token_urlsafe(48))"`

## 2. Chạy bằng Docker (khuyến nghị cho demo)
```bash
cp .env.example .env        # điền SECRET_KEY, GEMINI_API_KEY
docker compose up --build
```
- Lần chạy đầu tự nạp dữ liệu mẫu; dữ liệu lưu trong volume `petcare-data` (không mất khi tắt/bật container).
- Container chạy bằng người dùng không phải root, có `HEALTHCHECK` gọi `/api/health`.
- Muốn bắt đầu với CSDL trống thay vì dữ liệu mẫu: đặt `SEED_ON_FIRST_RUN=0` (khi đó cần tự tạo tài khoản quản trị).
- Xem log: `docker compose logs -f petcare` · Dừng: `docker compose down` (thêm `-v` nếu muốn XÓA cả dữ liệu).

## 3. Biến môi trường
| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `SECRET_KEY` | khóa demo (có cảnh báo) | Khóa ký JWT. **Bắt buộc đổi** khi triển khai thật |
| `GEMINI_API_KEY` | rỗng | Rỗng = AI chạy chế độ dự phòng (mẫu cố định) |
| `GEMINI_MODEL` | `gemini-3.5-flash` | Tên model Gemini |
| `GEMINI_TIMEOUT` | `30` | Giây chờ tối đa mỗi lần gọi |
| `AI_RATE_LIMIT_PER_MIN` | `20` | Lượt gọi AI/người dùng/phút |
| `LOGIN_MAX_FAILURES` | `5` | Số lần sai mật khẩu trước khi khóa 15 phút |
| `CORS_ORIGINS` | rỗng | Danh sách origin được phép (rỗng = chỉ cùng origin) |
| `DATABASE_PATH` | `./petcare.db` | Vị trí file SQLite |
| `BACKUP_DIR` | `./backups` | Thư mục sao lưu |

## 4. Sao lưu và khôi phục CSDL
```bash
python backend/db_tools.py backup --keep 10      # sao lưu, giữ 10 bản mới nhất
python backend/db_tools.py list
python backend/db_tools.py verify backups/<file>.db
python backend/db_tools.py restore backups/<file>.db --yes
```
- Dùng SQLite backup API nên an toàn ngay cả khi ứng dụng đang chạy.
- Khôi phục **luôn kiểm tra** bản sao lưu trước (integrity + khóa ngoại), tự sao lưu CSDL hiện tại thành `before_restore_*.db`, và từ chối nếu file hỏng.
- Nên dừng ứng dụng trước khi khôi phục.
- Docker: `docker compose exec petcare python /app/backend/db_tools.py backup` (bản sao lưu nằm trong volume `/data/backups`).
- Tự động hằng ngày (Linux, cron): `0 2 * * * cd /đường/dẫn && python backend/db_tools.py backup --keep 14`

## 5. Nâng cấp CSDL cũ
`create_all` chỉ tạo bảng còn thiếu, **không** thêm ràng buộc CHECK vào bảng đã có. Với CSDL cũ:
sao lưu → chạy `python backend/seed_data.py` để tạo lại (mất dữ liệu cũ) hoặc xuất dữ liệu cần giữ trước.
Với sản phẩm thật nên dùng công cụ migration (Alembic).

## 6. Danh sách kiểm tra trước khi đưa lên môi trường thật
- [ ] Đặt `SECRET_KEY` riêng; không commit `.env`
- [ ] **Đổi/xóa tài khoản demo** (`admin/admin123`, `letan/letan123`, `groomer/groomer123`) và ẩn nút đăng nhập nhanh trên giao diện
- [ ] Chạy sau reverse proxy HTTPS (Nginx/Caddy/dịch vụ cloud) để mã hóa đường truyền
- [ ] Cấu hình sao lưu định kỳ và thử khôi phục ít nhất một lần
- [ ] Giới hạn `CORS_ORIGINS` nếu tách frontend
- [ ] Đặt hạn mức/chi phí cho API key Gemini

## 7. Triển khai cloud (gợi ý)
Image Docker chạy được trên các dịch vụ hỗ trợ container (Render, Railway, Fly.io, Cloud Run…): trỏ tới `Dockerfile`, đặt biến môi trường ở mục 3, gắn volume/disk bền vững vào `/data`
(bắt buộc, vì SQLite lưu trong file; nếu dịch vụ không có disk bền vững thì dữ liệu mất khi khởi động lại).
> Nhóm chưa thử triển khai lên một dịch vụ cloud cụ thể; mục này chỉ là hướng dẫn chung.

## 8. Xử lý sự cố
| Hiện tượng | Nguyên nhân / cách xử lý |
|---|---|
| AI hiện nhãn "Mẫu dự phòng" | Chưa có `GEMINI_API_KEY`, hết quota, hoặc Gemini lỗi (xem log). Sau 3 lần lỗi liên tiếp hệ thống tạm bỏ qua Gemini 60 giây |
| HTTP 429 khi đăng nhập | Sai mật khẩu quá nhiều lần; chờ theo `Retry-After` |
| HTTP 429 khi dùng AI | Vượt `AI_RATE_LIMIT_PER_MIN` |
| HTTP 409 khi xóa | Dữ liệu đang được tham chiếu (vd. dịch vụ đã có lịch hẹn) |
| Cổng 8000 bị chiếm | Đổi cổng trong `docker-compose.yml` hoặc `run_app.py` |
