# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="RECEPTIONIST") # ADMIN, RECEPTIONIST, GROOMER
    created_at = Column(DateTime, default=datetime.utcnow)

class Owner(Base):
    __tablename__ = "owners"
    owner_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), index=True, nullable=False)
    phone = Column(String(20), index=True, nullable=False)
    address = Column(String(255), nullable=True)
    email = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    pets = relationship("Pet", back_populates="owner", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="owner")

class Pet(Base):
    __tablename__ = "pets"
    pet_id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.owner_id"), nullable=False)
    pet_name = Column(String(50), index=True, nullable=False)
    pet_type = Column(String(20), nullable=False) # CHO, MEO
    breed = Column(String(50), nullable=True)
    age = Column(Integer, nullable=True)
    weight = Column(Float, nullable=False, default=3.0)
    medical_history = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("Owner", back_populates="pets")
    appointments = relationship("Appointment", back_populates="pet", cascade="all, delete-orphan")
    care_records = relationship("CareRecord", back_populates="pet")
    vaccinations = relationship("VaccinationReminder", back_populates="pet")

class Service(Base):
    __tablename__ = "services"
    __table_args__ = (CheckConstraint("price >= 0", name="ck_service_price"),
                      CheckConstraint("duration_minutes > 0", name="ck_service_duration"))
    service_id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(100), nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=60)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)

    appointments = relationship("Appointment", back_populates="service")
    invoice_items = relationship("InvoiceItem", back_populates="service")

class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (CheckConstraint("status IN ('CONFIRMED', 'COMPLETED', 'CANCELLED')", name="ck_appointment_status"),
                      CheckConstraint("end_time > start_time", name="ck_appointment_time_order"))
    appointment_id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.pet_id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.service_id"), nullable=False)
    groomer_name = Column(String(50), nullable=False, default="Thợ Minh")
    appointment_date = Column(String(20), nullable=False) # YYYY-MM-DD
    start_time = Column(String(10), nullable=False) # HH:MM
    end_time = Column(String(10), nullable=False)   # HH:MM
    status = Column(String(20), default="CONFIRMED") # CONFIRMED, COMPLETED, CANCELLED
    notes = Column(Text, nullable=True)

    pet = relationship("Pet", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")
    care_record = relationship("CareRecord", back_populates="appointment", uselist=False)
    invoice = relationship("Invoice", back_populates="appointment", uselist=False)

class CareRecord(Base):
    __tablename__ = "care_records"
    care_id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.pet_id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.appointment_id"), nullable=True)
    weight_after = Column(Float, nullable=True)
    skin_condition = Column(Text, nullable=True)
    behavior_notes = Column(Text, nullable=True)
    advice = Column(Text, nullable=True)
    record_date = Column(DateTime, default=datetime.utcnow)

    pet = relationship("Pet", back_populates="care_records")
    appointment = relationship("Appointment", back_populates="care_record")

class VaccinationReminder(Base):
    __tablename__ = "vaccination_reminders"
    __table_args__ = (CheckConstraint("status IN ('PENDING', 'DONE')", name="ck_vaccine_status"),)
    reminder_id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.pet_id"), nullable=False)
    vaccine_name = Column(String(100), nullable=False)
    last_date = Column(String(20), nullable=True)
    next_due_date = Column(String(20), nullable=False)
    status = Column(String(20), default="PENDING") # PENDING, DONE

    pet = relationship("Pet", back_populates="vaccinations")

class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (CheckConstraint("status IN ('PAID', 'PARTIAL', 'UNPAID', 'CANCELLED')", name="ck_invoice_status"),
                      CheckConstraint("total_amount >= 0 AND final_amount >= 0 AND discount >= 0", name="ck_invoice_amounts"))
    invoice_id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.owner_id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.appointment_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Float, nullable=False, default=0.0)
    discount = Column(Float, default=0.0)
    final_amount = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), default="PAID") # PAID, UNPAID, CANCELLED

    owner = relationship("Owner", back_populates="invoices")
    appointment = relationship("Appointment", back_populates="invoice")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    __table_args__ = (CheckConstraint("quantity >= 1 AND unit_price >= 0", name="ck_item_values"),)
    item_id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.invoice_id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.service_id"), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    invoice = relationship("Invoice", back_populates="items")
    service = relationship("Service", back_populates="invoice_items")

class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (CheckConstraint("amount > 0", name="ck_payment_amount"),)
    payment_id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.invoice_id"), nullable=False)
    payment_method = Column(String(30), default="TIEN_MAT") # TIEN_MAT, CHUYEN_KHOAN, THE
    payment_date = Column(DateTime, default=datetime.utcnow)
    amount = Column(Float, nullable=False)
    transaction_code = Column(String(50), nullable=True)

    invoice = relationship("Invoice", back_populates="payments")

class AILog(Base):
    """Nhật ký gọi AI để kiểm toán và đo chất lượng. KHÔNG lưu nội dung câu hỏi/câu trả lời (quyền riêng tư)."""
    __tablename__ = "ai_logs"
    log_id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    username = Column(String(50), nullable=False)
    endpoint = Column(String(20), nullable=False)       # reminder | summary | ask
    pet_id = Column(Integer, ForeignKey("pets.pet_id"), nullable=True)
    source = Column(String(20), nullable=False)         # gemini | fallback | guardrail
    guardrail = Column(String(30), nullable=True)       # emergency | out_of_scope | prompt_injection | output_policy
    need_vet = Column(Boolean, default=False)
    latency_ms = Column(Integer, default=0)


class ServicePackage(Base):
    __tablename__ = "service_packages"
    __table_args__ = (CheckConstraint("price >= 0", name="ck_package_price"),)
    package_id = Column(Integer, primary_key=True, index=True)
    package_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)          # giá bán của cả gói
    is_active = Column(Boolean, default=True)
    items = relationship("ServicePackageItem", back_populates="package", cascade="all, delete-orphan")

class ServicePackageItem(Base):
    __tablename__ = "service_package_items"
    __table_args__ = (CheckConstraint("quantity >= 1", name="ck_package_item_qty"),)
    item_id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("service_packages.package_id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.service_id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    package = relationship("ServicePackage", back_populates="items")
    service = relationship("Service")
