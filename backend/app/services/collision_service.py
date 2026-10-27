# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from ..models import Appointment

def check_groomer_collision(
    db: Session,
    groomer_name: str,
    appointment_date: str,
    new_start: str,
    new_end: str,
    exclude_id: int = None
) -> bool:
    """
    Thuật toán kiểm tra trùng lịch Groomer:
    Khoảng thời gian (new_start, new_end) bị trùng với lịch hiện có (start_time, end_time) nếu:
    start_time < new_end AND end_time > new_start
    """
    query = db.query(Appointment).filter(
        Appointment.groomer_name == groomer_name,
        Appointment.appointment_date == appointment_date,
        Appointment.status != "CANCELLED",
        Appointment.start_time < new_end,
        Appointment.end_time > new_start
    )
    if exclude_id:
        query = query.filter(Appointment.appointment_id != exclude_id)
        
    conflicting = query.first()
    return conflicting is not None
