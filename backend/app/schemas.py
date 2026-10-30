# -*- coding: utf-8 -*-
import re
from typing import List, Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

def _check_time(v):
    if v is not None and not _TIME_RE.match(v):
        raise ValueError("Giờ phải có định dạng HH:MM (00:00 - 23:59)")
    return v

def _check_date(v):
    if v is not None:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Ngày phải có định dạng YYYY-MM-DD hợp lệ")
    return v

# AUTH & USER
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str
    role: str = "RECEPTIONIST"

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserOut(UserBase):
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    full_name: str

class LoginRequest(BaseModel):
    username: str
    password: str

# OWNER
class OwnerBase(BaseModel):
    full_name: str
    phone: str
    address: Optional[str] = None
    email: Optional[str] = None

class OwnerCreate(OwnerBase):
    pass

class OwnerUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None

class OwnerOut(OwnerBase):
    owner_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# PET
class PetBase(BaseModel):
    owner_id: int
    pet_name: str
    pet_type: str
    breed: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=40)
    weight: float = Field(3.0, gt=0, le=150)
    medical_history: Optional[str] = None

class PetCreate(PetBase):
    pass

class PetUpdate(BaseModel):
    owner_id: Optional[int] = None
    pet_name: Optional[str] = None
    pet_type: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=40)
    weight: Optional[float] = Field(None, gt=0, le=150)
    medical_history: Optional[str] = None

class PetOut(PetBase):
    pet_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# SERVICE
class ServiceBase(BaseModel):
    service_name: str
    duration_minutes: int = 60
    price: float
    description: Optional[str] = None

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    service_name: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None

class ServiceOut(ServiceBase):
    service_id: int
    class Config:
        from_attributes = True

# APPOINTMENT
class AppointmentBase(BaseModel):
    pet_id: int
    service_id: int
    groomer_name: str = "Thợ Minh"
    appointment_date: str # YYYY-MM-DD
    start_time: str       # HH:MM
    end_time: str         # HH:MM
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    @field_validator("start_time", "end_time")
    @classmethod
    def _validate_time(cls, v):
        return _check_time(v)

    @field_validator("appointment_date")
    @classmethod
    def _validate_date(cls, v):
        return _check_date(v)

    @model_validator(mode="after")
    def _validate_order(self):
        if self.end_time <= self.start_time:
            raise ValueError("Giờ kết thúc phải sau giờ bắt đầu")
        return self

class AppointmentUpdate(BaseModel):
    groomer_name: Optional[str] = None
    appointment_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[Literal["CONFIRMED", "COMPLETED", "CANCELLED"]] = None
    notes: Optional[str] = None

    @field_validator("start_time", "end_time")
    @classmethod
    def _validate_time(cls, v):
        return _check_time(v)

    @field_validator("appointment_date")
    @classmethod
    def _validate_date(cls, v):
        return _check_date(v)

class AppointmentOut(AppointmentBase):
    appointment_id: int
    status: str
    class Config:
        from_attributes = True

# CARE RECORD
class CareRecordBase(BaseModel):
    pet_id: int
    appointment_id: Optional[int] = None
    weight_after: Optional[float] = None
    skin_condition: Optional[str] = None
    behavior_notes: Optional[str] = None
    advice: Optional[str] = None

class CareRecordCreate(CareRecordBase):
    pass

class CareRecordUpdate(BaseModel):
    weight_after: Optional[float] = Field(None, gt=0)
    skin_condition: Optional[str] = None
    behavior_notes: Optional[str] = None
    advice: Optional[str] = None

class CareRecordOut(CareRecordBase):
    care_id: int
    record_date: datetime
    class Config:
        from_attributes = True

# VACCINATION REMINDER
class VaccinationBase(BaseModel):
    pet_id: int
    vaccine_name: str
    last_date: Optional[str] = None
    next_due_date: str
    status: str = "PENDING"

class VaccinationCreate(VaccinationBase):
    pass

class VaccinationOut(VaccinationBase):
    reminder_id: int
    class Config:
        from_attributes = True

# INVOICE
class InvoiceItemCreate(BaseModel):
    service_id: int
    quantity: int = Field(1, ge=1)
    unit_price: Optional[float] = Field(None, ge=0)   # bỏ trống = lấy đơn giá hiện hành của dịch vụ

class InvoiceCreate(BaseModel):
    owner_id: int
    appointment_id: Optional[int] = None
    discount: float = Field(0.0, ge=0)
    payment_method: str = "TIEN_MAT"
    paid_amount: Optional[float] = Field(None, ge=0)   # bỏ trống = chưa thu; có thể ghi nhận tiền trả ngay
    items: List[InvoiceItemCreate] = Field(..., min_length=1)

class InvoiceItemOut(BaseModel):
    item_id: int
    service_id: int
    quantity: int
    unit_price: float
    subtotal: float
    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    payment_method: str = "TIEN_MAT"
    transaction_code: Optional[str] = None

class PaymentOut(BaseModel):
    payment_id: int
    payment_method: str
    payment_date: datetime
    amount: float
    transaction_code: Optional[str] = None
    class Config:
        from_attributes = True

class InvoiceOut(BaseModel):
    invoice_id: int
    owner_id: int
    appointment_id: Optional[int] = None
    created_at: datetime
    total_amount: float
    discount: float
    final_amount: float
    status: str                      # PAID | PARTIAL | UNPAID | CANCELLED
    paid_amount: float = 0.0
    remaining: float = 0.0
    items: List[InvoiceItemOut] = []
    payments: List[PaymentOut] = []
    class Config:
        from_attributes = True

# DASHBOARD STATS
class DashboardStats(BaseModel):
    total_owners: int
    total_pets: int
    total_appointments: int
    total_revenue: float
    retention_rate: float
    pending_appointments: int
    upcoming_vaccines: int
    total_debt: float = 0.0

# AI
class AIReminderRequest(BaseModel):
    pet_id: int
    kind: Literal["appointment", "vaccination"] = "appointment"
    appointment_id: Optional[int] = None
    reminder_id: Optional[int] = None

class AIAskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    pet_id: Optional[int] = None

    @field_validator("question")
    @classmethod
    def _strip(cls, v):
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Câu hỏi quá ngắn")
        return v

class AIResponse(BaseModel):
    content: str
    warning: str
    need_vet: bool
    source: str
    guardrail: Optional[str] = None

# SERVICE PACKAGE
class PackageItemIn(BaseModel):
    service_id: int
    quantity: int = Field(1, ge=1)

class PackageCreate(BaseModel):
    package_name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    is_active: bool = True
    items: List[PackageItemIn] = Field(..., min_length=1)

class PackageUpdate(BaseModel):
    package_name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None
    items: Optional[List[PackageItemIn]] = Field(None, min_length=1)

class PackageItemOut(BaseModel):
    service_id: int
    service_name: str
    quantity: int
    unit_price: float

class PackageOut(BaseModel):
    package_id: int
    package_name: str
    description: Optional[str] = None
    price: float
    is_active: bool
    original_price: float      # tổng giá lẻ các dịch vụ trong gói
    saving: float              # tiết kiệm = giá lẻ - giá gói
    items: List[PackageItemOut]
