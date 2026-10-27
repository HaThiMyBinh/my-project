# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Test không bao giờ gọi Gemini thật: đặt key rỗng TRƯỚC khi import app (dotenv không ghi đè biến đã có)
os.environ["GEMINI_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.auth import hash_password
from app.database import Base, get_db
from app.main import app

_PW_HASH = hash_password("pass1234")  # hash 1 lần cho cả phiên test


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):          # giống engine thật: bật kiểm tra khóa ngoại
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    db.add_all([
        models.User(username="admin", password_hash=_PW_HASH, full_name="Admin", role="ADMIN"),
        models.User(username="letan", password_hash=_PW_HASH, full_name="Lễ tân", role="RECEPTIONIST"),
        models.User(username="groomer", password_hash=_PW_HASH, full_name="Thợ Minh", role="GROOMER"),
        models.Owner(full_name="Chị Hoàng Thị Lan", phone="0988123456", address="123 Cầu Giấy", email="lan@example.com"),
        models.Service(service_name="Tắm spa", duration_minutes=60, price=200000),
        models.Service(service_name="Cắt tỉa lông", duration_minutes=90, price=150000),
    ])
    db.commit()
    db.add(models.Pet(owner_id=1, pet_name="Bé Bơ", pet_type="CHO", breed="Poodle", age=2, weight=4.5,
                      medical_history="Da bụng nhạy cảm"))
    db.commit()

    def override_get_db():
        try:
            yield db
        except Exception:
            db.rollback()               # giống get_db thật: lỗi thì rollback, request sau vẫn dùng được
            raise

    app.dependency_overrides[get_db] = override_get_db
    yield db
    app.dependency_overrides.clear()
    db.close()
    engine.dispose()


@pytest.fixture(autouse=True)
def reset_global_state():
    """Cache/ngắt mạch AI và bộ giới hạn tần suất là trạng thái toàn cục: xóa trước mỗi test để test độc lập."""
    from app.routers import ai as ai_router
    from app.routers import auth as auth_router
    from app.services import ai_service
    ai_service.reset_state()
    ai_service.RETRY_DELAY = 0
    ai_router.ai_limiter.reset()
    auth_router.login_limiter.reset()
    yield


@pytest.fixture()
def client(db_session):
    return TestClient(app)


@pytest.fixture()
def auth(client):
    """auth('admin') -> header Authorization cho vai trò tương ứng."""
    def _auth(username="admin"):
        r = client.post("/api/auth/login", json={"username": username, "password": "pass1234"})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}
    return _auth
