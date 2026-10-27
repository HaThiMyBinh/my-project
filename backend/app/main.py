# -*- coding: utf-8 -*-
import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from . import config  # noqa: F401  (nạp .env trước khi import các module khác)
from .database import engine, Base
from .routers import auth, owners, pets, services, appointments, care_records, vaccinations, invoices, analytics, ai, packages

logger = logging.getLogger("petcare")

# Auto-create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PetCare Spa Management API (Nhóm 6)",
    description="Hệ thống Quản lý Thú cưng và Lịch Chăm sóc tích hợp AI - Đề tài 20",
    version="3.0.0"
)

# CORS: giao diện được phục vụ cùng origin nên mặc định không mở; đặt CORS_ORIGINS=http://a.com,http://b.com nếu tách frontend
_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    return response

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Vi phạm ràng buộc CSDL (khóa ngoại, CHECK, UNIQUE) -> 409 thay vì 500."""
    logger.warning("Vi phạm ràng buộc CSDL tại %s: %s", request.url.path, exc.orig)
    return JSONResponse(status_code=409, content={"detail": "Thao tác vi phạm ràng buộc dữ liệu (dữ liệu đang được sử dụng hoặc không hợp lệ)."})

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Chi tiết lỗi chỉ ghi log phía server, không trả về cho client
    logger.exception("Lỗi không xử lý được tại %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Đã xảy ra lỗi máy chủ nội bộ. Vui lòng thử lại sau."}
    )

# Include Routers
app.include_router(auth.router)
app.include_router(owners.router)
app.include_router(pets.router)
app.include_router(services.router)
app.include_router(packages.router)
app.include_router(appointments.router)
app.include_router(care_records.router)
app.include_router(vaccinations.router)
app.include_router(invoices.router)
app.include_router(analytics.router)
app.include_router(ai.router)

# Mount Frontend if exists
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")
if os.path.exists(frontend_path):
    app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")

@app.get("/api/health", tags=["System"])
def health():
    """Kiểm tra sống (dùng cho Docker healthcheck / giám sát)."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return JSONResponse(status_code=200 if db_ok else 503, content={"status": "ok" if db_ok else "degraded", "database": db_ok})

@app.get("/")
def root():
    return {
        "project": "Hệ thống Quản lý Thú cưng PetCare Spa - Nhóm 6",
        "authors": ["Hà Thị Mỹ Bình", "Nguyễn Thị Giang"],
        "docs_url": "/docs",
        "frontend_ui": "/app/index.html",
        "status": "Running smoothly"
    }
