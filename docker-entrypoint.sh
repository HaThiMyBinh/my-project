#!/bin/sh
# Lần chạy đầu (chưa có CSDL): nạp dữ liệu mẫu. Các lần sau giữ nguyên dữ liệu trong volume /data.
set -e
cd /app/backend

if [ ! -f "${DATABASE_PATH}" ] && [ "${SEED_ON_FIRST_RUN:-1}" = "1" ]; then
  echo "[petcare] Chưa có CSDL -> nạp dữ liệu mẫu"
  python seed_data.py
fi

if [ -z "${SECRET_KEY}" ]; then
  echo "[petcare] CẢNH BÁO: chưa đặt SECRET_KEY, đang dùng khóa mặc định (chỉ phù hợp demo)"
fi
if [ -z "${GEMINI_API_KEY}" ]; then
  echo "[petcare] Chưa đặt GEMINI_API_KEY -> AI chạy ở chế độ dự phòng"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
