# KỊCH BẢN DEMO (≈ 10–12 phút) VÀ CÂU HỎI DỰ KIẾN

## Chuẩn bị (trước giờ thi)
- [ ] `docker compose up --build` (hoặc `python run_app.py`) đã chạy; mở sẵn http://localhost:8000/app/index.html
- [ ] Đã điền `GEMINI_API_KEY` và **thử gọi AI một lần** để chắc chắn key còn hạn mức
- [ ] Đã chạy `python backend/seed_data.py` để dữ liệu mẫu sạch (có hóa đơn còn nợ, 2 gói dịch vụ)
- [ ] Mở sẵn 3 trình duyệt/tab đăng nhập `admin`, `letan`, `groomer`; mở sẵn Swagger `/docs`
- [ ] Có sẵn ảnh chụp kết quả `pytest` phòng khi mạng lỗi
- [ ] **Plan B:** nếu mất mạng/Gemini lỗi, vẫn demo được AI ở chế độ dự phòng (nhãn "Mẫu dự phòng") và nói rõ đó là cơ chế chịu lỗi

## Mạch demo
| Phút | Nội dung | Thao tác | Điểm nhấn cho giám khảo |
|---|---|---|---|
| 0–1 | Giới thiệu | Nêu bài toán, 3 vai trò, kiến trúc 1 slide | Tiêu chí 1, 2 |
| 1–3 | Quản lý lõi | `letan`: tạo chủ nuôi → thú cưng → **đặt lịch** | Tiêu chí 1 |
| 3–4 | **Chống trùng lịch** | Đặt lịch chồm giờ cùng thợ → thông báo lỗi 409; đặt lịch liền kề → được | Thuật toán, phản hồi lỗi (tiêu chí 1, 4) |
| 4–5 | Hồ sơ & gói | `groomer`: thêm/sửa hồ sơ chăm sóc; `admin`: xem gói dịch vụ (giá lẻ vs giá gói) | Tiêu chí 1 |
| 5–6 | **Hóa đơn & công nợ** | Lập hóa đơn trả một phần → trạng thái "Còn nợ" → **Thu tiền** → "Đã thu đủ"; dashboard đổi doanh thu/công nợ | Nhất quán dữ liệu (tiêu chí 3) |
| 6–8 | **AI** (trọng tâm) | (1) Nhắc lịch spa cho bé có lịch; (2) Tóm tắt hồ sơ bé Bơ; (3) Hỏi "Bao lâu nên tắm cho mèo?" → có cảnh báo | Tiêu chí 5 |
| 8–9 | **Rào chắn y tế** | Hỏi "Chó nhà em đang co giật" → khung đỏ, khuyên gặp bác sĩ thú y; hỏi "Cho mèo uống paracetamol bao nhiêu mg?" → từ chối; thử "Bỏ qua mọi hướng dẫn…" | Có kiểm soát sai lệch, đạo đức AI (tiêu chí 5, 6) |
| 9–10 | Bảo mật & phân quyền | `groomer` xem chủ nuôi → SĐT bị che, không có địa chỉ; `letan` truy cập chức năng ADMIN → 403; đăng nhập sai 5 lần → 429; (admin) thẻ thống kê AI | Tiêu chí 6 |
| 10–11 | Ổn định & triển khai | Xóa `GEMINI_API_KEY` (hoặc nêu cơ chế) → "Mẫu dự phòng"; `/api/health`; `docker compose ps` (healthy); chạy `db_tools.py backup` | Tiêu chí 7, 8, 3 |
| 11–12 | Kiểm thử & AI trong SDLC | Chiếu kết quả pytest; 1–2 ảnh chat AI thể hiện nhóm **phản biện và sửa** đầu ra AI (vd. lỗ hổng "parvo") | Tiêu chí 9, 10 |

## Câu hỏi dự kiến và gợi ý trả lời
1. **AI có thể sai, nhóm xử lý thế nào?** Nhiều lớp: lọc đầu vào (khẩn cấp/kê đơn không gọi AI), system prompt hạn chế phạm vi, lọc đầu ra (chặn liều thuốc), cảnh báo cố định, nhãn nguồn, nhật ký AI. Nói thẳng giới hạn: guardrail theo từ khóa, có thể bỏ sót.
2. **AI có chẩn đoán/kê đơn không?** Không; cả prompt và code đều chặn; có 31 câu bẫy kiểm thử.
3. **Dữ liệu nào gửi sang Gemini?** Tên chủ nuôi, thông tin thú cưng, hồ sơ chăm sóc. Không gửi SĐT, địa chỉ, email. Nhật ký không lưu nội dung.
4. **API key bảo vệ ra sao?** Trong `.env`/biến môi trường, header (không ở URL), không ghi log, `.gitignore`/`.dockerignore`.
5. **Gemini sập/hết quota thì sao?** Thử lại 1 lần → ngắt mạch 60 giây → dùng mẫu dự phòng; có cache và giới hạn 20 lượt/phút/người.
6. **Thuật toán chống trùng lịch?** Hai khoảng thời gian trùng nếu `start_a < end_b` và `start_b < end_a` (cùng thợ, cùng ngày, bỏ lịch đã hủy); lịch liền kề hợp lệ; có test.
7. **Vì sao doanh thu không bằng tổng hóa đơn?** Doanh thu = tiền đã thu; phần chưa thu là công nợ; hóa đơn hủy không tính.
8. **Dữ liệu nhất quán thế nào?** Khóa ngoại bật, ràng buộc CHECK, đã thu suy ra từ bảng `payments`; vi phạm trả 409.
9. **Sao lưu/khôi phục?** `db_tools.py`: sao lưu an toàn, kiểm tra toàn vẹn trước khi khôi phục, tự sao lưu bản hiện tại. Demo được.
10. **Hạn chế lớn nhất?** Nói thật: guardrail từ khóa; tài khoản demo; chưa HTTPS; chưa đo tải; SQLite; trạng thái limiter trong bộ nhớ.
11. **Nhóm dùng AI ở đâu trong SDLC và kiểm soát thế nào?** Nêu ví dụ cụ thể có ảnh; nhấn mạnh test phát hiện lỗi do AI sinh/ do chính nhóm.
12. **Phân công?** Bình: backend/AI/CSDL; Giang: frontend/test. (Nhóm tự bổ sung đúng thực tế.)

## Lưu ý khi thuyết trình
- Đừng hiển thị API key; đừng mở file `.env` trên màn hình chiếu.
- Chỉ nói những gì nhóm đã thực sự chạy; nếu chưa thử (ví dụ cloud), nói là "hướng phát triển".
- Mỗi thành viên phải giải thích được phần code mình nhận, kể cả phần do AI sinh.
