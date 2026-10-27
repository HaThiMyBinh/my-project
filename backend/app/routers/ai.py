# -*- coding: utf-8 -*-
"""API AI: nhắc lịch, tóm tắt hồ sơ chăm sóc, hỏi đáp chăm sóc cơ bản (Gemini)."""
import logging
import os
import time
from collections import Counter
from datetime import date
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_role
from ..database import get_db
from ..models import AILog, Appointment, CareRecord, Owner, Pet, Service, VaccinationReminder
from ..schemas import AIAskRequest, AIReminderRequest, AIResponse
from ..services import ai_service
from ..services.rate_limit import SlidingWindowLimiter

logger = logging.getLogger("petcare.ai")
router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])

# Giới hạn số lượt gọi AI mỗi người dùng để tránh lạm dụng và tốn quota Gemini
ai_limiter = SlidingWindowLimiter(max_events=int(os.getenv("AI_RATE_LIMIT_PER_MIN", "20")), window_seconds=60)


def ai_guard(current_user=Depends(get_current_user)):
    allowed, retry = ai_limiter.check_and_hit(current_user.username)
    if not allowed:
        raise HTTPException(status_code=429, detail=f"Bạn gọi AI quá nhanh. Vui lòng thử lại sau {retry} giây.",
                            headers={"Retry-After": str(retry)})
    return current_user


def _audit(db: Session, user, endpoint: str, result: Dict, started: float, pet_id: Optional[int] = None) -> Dict:
    """Ghi nhật ký (không lưu nội dung). Lỗi ghi log không được làm hỏng phản hồi AI."""
    try:
        db.add(AILog(username=user.username, endpoint=endpoint, pet_id=pet_id, source=result["source"],
                     guardrail=result.get("guardrail"), need_vet=bool(result["need_vet"]),
                     latency_ms=int((time.perf_counter() - started) * 1000)))
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Không ghi được ai_logs")
    return result


def _get_pet(db: Session, pet_id: int) -> Pet:
    pet = db.query(Pet).filter(Pet.pet_id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Thú cưng không tồn tại")
    return pet


def _pet_dict(pet: Pet) -> Dict:
    # Chỉ gửi dữ liệu cần thiết, KHÔNG gồm thông tin liên hệ của chủ nuôi
    return {
        "pet_name": pet.pet_name, "pet_type": pet.pet_type, "breed": pet.breed,
        "age": pet.age, "weight": pet.weight, "medical_history": pet.medical_history,
    }


def _records(db: Session, pet_id: int, limit: int = 10) -> List[Dict]:
    rows = (db.query(CareRecord).filter(CareRecord.pet_id == pet_id)
            .order_by(CareRecord.record_date.desc()).limit(limit).all())
    return [{
        "record_date": r.record_date.strftime("%Y-%m-%d") if r.record_date else None,
        "weight_after": r.weight_after, "skin_condition": r.skin_condition,
        "behavior_notes": r.behavior_notes, "advice": r.advice,
    } for r in rows]


@router.get("/status")
def ai_status(current_user=Depends(get_current_user)):
    client = ai_service.get_client()
    return {
        "configured": client.configured,
        "model": client.model,
        "warning": ai_service.DISCLAIMER,
        "mode": "gemini" if client.configured else "fallback (chưa cấu hình GEMINI_API_KEY)",
    }


@router.post("/reminder", response_model=AIResponse)
def generate_reminder(req: AIReminderRequest, db: Session = Depends(get_db),
                      current_user=Depends(ai_guard)):
    started = time.perf_counter()
    pet = _get_pet(db, req.pet_id)
    owner = db.query(Owner).filter(Owner.owner_id == pet.owner_id).first()
    owner_name = owner.full_name if owner else "Quý khách"

    if req.kind == "vaccination":
        q = db.query(VaccinationReminder).filter(
            VaccinationReminder.pet_id == pet.pet_id, VaccinationReminder.status == "PENDING")
        if req.reminder_id:
            q = q.filter(VaccinationReminder.reminder_id == req.reminder_id)
        vac = q.order_by(VaccinationReminder.next_due_date.asc()).first()
        if not vac:
            raise HTTPException(status_code=404, detail="Không có lịch tiêm nhắc đang chờ cho thú cưng này")
        vaccine = {"vaccine_name": vac.vaccine_name, "next_due_date": vac.next_due_date, "last_date": vac.last_date}
        result = ai_service.generate_reminder(owner_name, _pet_dict(pet), vaccine=vaccine)
        return _audit(db, current_user, "reminder", result, started, pet.pet_id)

    q = db.query(Appointment).filter(Appointment.pet_id == pet.pet_id)
    if req.appointment_id:
        q = q.filter(Appointment.appointment_id == req.appointment_id)
    else:
        q = q.filter(Appointment.status == "CONFIRMED", Appointment.appointment_date >= date.today().isoformat())
    app = q.order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc()).first()
    if not app:
        raise HTTPException(status_code=404, detail="Không có lịch hẹn sắp tới cho thú cưng này")
    srv = db.query(Service).filter(Service.service_id == app.service_id).first()
    appointment = {
        "service_name": srv.service_name if srv else "dịch vụ chăm sóc",
        "appointment_date": app.appointment_date, "start_time": app.start_time,
        "end_time": app.end_time, "groomer_name": app.groomer_name,
    }
    result = ai_service.generate_reminder(owner_name, _pet_dict(pet), appointment=appointment)
    return _audit(db, current_user, "reminder", result, started, pet.pet_id)


@router.post("/summary/{pet_id}", response_model=AIResponse)
def summarize_pet(pet_id: int, db: Session = Depends(get_db), current_user=Depends(ai_guard)):
    started = time.perf_counter()
    pet = _get_pet(db, pet_id)
    result = ai_service.summarize_care_history(_pet_dict(pet), _records(db, pet.pet_id))
    return _audit(db, current_user, "summary", result, started, pet.pet_id)


@router.post("/ask", response_model=AIResponse)
def ask_question(req: AIAskRequest, db: Session = Depends(get_db), current_user=Depends(ai_guard)):
    started = time.perf_counter()
    pet: Optional[Dict] = None
    records: Optional[List[Dict]] = None
    if req.pet_id is not None:
        p = _get_pet(db, req.pet_id)
        pet, records = _pet_dict(p), _records(db, p.pet_id, limit=5)
    result = ai_service.answer_question(req.question, pet, records)
    return _audit(db, current_user, "ask", result, started, req.pet_id)


@router.get("/logs")
def ai_logs(limit: int = 50, db: Session = Depends(get_db), current_user=Depends(require_role(["ADMIN"]))):
    """Thống kê sử dụng AI (chỉ ADMIN): tỷ lệ guardrail, fallback, độ trễ. Không chứa nội dung hội thoại."""
    rows = db.query(AILog).order_by(AILog.log_id.desc()).all()
    total = len(rows)
    return {
        "total": total,
        "by_source": dict(Counter(x.source for x in rows)),
        "by_guardrail": dict(Counter(x.guardrail for x in rows if x.guardrail)),
        "need_vet_count": sum(1 for x in rows if x.need_vet),
        "avg_latency_ms": round(sum(x.latency_ms or 0 for x in rows) / total, 1) if total else 0,
        "recent": [{"created_at": x.created_at, "username": x.username, "endpoint": x.endpoint, "source": x.source,
                    "guardrail": x.guardrail, "need_vet": x.need_vet, "latency_ms": x.latency_ms}
                   for x in rows[:max(1, min(limit, 200))]],
    }
