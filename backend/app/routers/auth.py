# -*- coding: utf-8 -*-
import os
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import Token, LoginRequest, UserOut
from ..auth import verify_password, create_access_token, get_current_user
from ..services.rate_limit import SlidingWindowLimiter

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Khóa tạm khi đăng nhập sai nhiều lần (theo tài khoản + IP) để chống dò mật khẩu
login_limiter = SlidingWindowLimiter(max_events=int(os.getenv("LOGIN_MAX_FAILURES", "5")), window_seconds=15 * 60)

@router.post("/login", response_model=Token)
def login(form_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    key = f"{form_data.username.lower()}|{request.client.host if request.client else '?'}"
    wait = login_limiter.retry_after(key)
    if wait:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=f"Đăng nhập sai quá nhiều lần. Vui lòng thử lại sau {wait} giây.",
                            headers={"Retry-After": str(wait)})
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        login_limiter.hit(key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác"
        )
    login_limiter.reset(key)
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
        "full_name": user.full_name
    }

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
