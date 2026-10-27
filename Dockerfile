# PetCare Spa - image chạy cả API và giao diện (FastAPI phục vụ /app)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/data/petcare.db \
    BACKUP_DIR=/data/backups

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend
COPY frontend frontend
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# chạy bằng người dùng không phải root; dữ liệu nằm trong volume /data
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /data/backups \
    && chown -R app:app /data /app \
    && chmod +x /usr/local/bin/docker-entrypoint.sh
USER app

VOLUME /data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else 1)"

ENTRYPOINT ["docker-entrypoint.sh"]
