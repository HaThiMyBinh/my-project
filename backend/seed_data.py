# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models import User, Owner, Pet, Service, Appointment, CareRecord, VaccinationReminder, Invoice, InvoiceItem, Payment, ServicePackage, ServicePackageItem
from app.auth import hash_password

def seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("Seeding Users...")
    users = [
        User(username="admin", password_hash=hash_password("admin123"), full_name="Hà Thị Mỹ Bình (Chủ tiệm)", role="ADMIN"),
        User(username="letan", password_hash=hash_password("letan123"), full_name="Nguyễn Thị Giang (Lễ tân)", role="RECEPTIONIST"),
        User(username="groomer", password_hash=hash_password("groomer123"), full_name="Thợ Minh (Groomer)", role="GROOMER")
    ]
    db.add_all(users)
    db.commit()

    print("Seeding Owners...")
    owners = [
        Owner(full_name="Chị Hoàng Thị Lan", phone="0988123456", address="123 Cầu Giấy, Hà Nội", email="lan.hoang@gmail.com"),
        Owner(full_name="Anh Trần Quốc Tuấn", phone="0912456789", address="45 Nguyễn Trãi, Thanh Xuân, Hà Nội", email="tuan.tran@gmail.com"),
        Owner(full_name="Cô Lê Thanh Hương", phone="0903112233", address="88 Láng Hạ, Đống Đa, Hà Nội", email="huong.le@yahoo.com"),
        Owner(full_name="Bác Phạm Văn Hùng", phone="0977445566", address="12 Hoàng Hoa Thám, Ba Đình", email="hung.pham@gmail.com")
    ]
    db.add_all(owners)
    db.commit()

    print("Seeding Pets...")
    pets = [
        Pet(owner_id=1, pet_name="Bé Bơ", pet_type="CHO", breed="Poodle Trắng", age=2, weight=4.5, medical_history="Da bụng nhạy cảm, sợ sấy to"),
        Pet(owner_id=1, pet_name="Bé Đậu", pet_type="CHO", breed="Poodle Nâu", age=1, weight=3.8, medical_history="Khỏe mạnh bình thường"),
        Pet(owner_id=2, pet_name="Bé Miu", pet_type="MEO", breed="Anh Lông Ngắn", age=3, weight=5.2, medical_history="Từng bị nấm da nhẹ"),
        Pet(owner_id=3, pet_name="Bé Kem", pet_type="CHO", breed="Corgi", age=2, weight=11.5, medical_history="Dị ứng xà phòng thơm nồng"),
        Pet(owner_id=4, pet_name="Bé Lu", pet_type="CHO", breed="Golden Retriever", age=4, weight=28.0, medical_history="Khớp háng hơi yếu")
    ]
    db.add_all(pets)
    db.commit()

    print("Seeding Services...")
    services = [
        Service(service_name="Tắm Sấy & Vệ Sinh Tai Móng Cơ Bản", duration_minutes=45, price=150000, description="Tắm dưỡng thảo mộc, sấy êm, vệ sinh tai và cắt dũa móng."),
        Service(service_name="Combo Spa Cắt Tỉa Tạo Kiểu Toàn Diện", duration_minutes=90, price=320000, description="Gội xả chuyên sâu, massage thư giãn, cắt tỉa form chuẩn Poodle/Corgi."),
        Service(service_name="Gỡ Rối & Dưỡng Lông Mượt Cao Cấp", duration_minutes=60, price=200000, description="Dầu dưỡng keratin phục hồi lông xơ rối, bóng mượt tự nhiên."),
        Service(service_name="Vệ Sinh Răng Miệng & Vắt Tuyến Hôi", duration_minutes=30, price=100000, description="Làm sạch mảng bám men răng và vệ sinh tuyến hôi an toàn."),
        Service(service_name="Tắm Trị Liệu Nấm Da Thảo Dược", duration_minutes=60, price=250000, description="Ngâm bồn thảo dược diệt nấm khuẩn, làm dịu vùng da viêm đỏ.")
    ]
    db.add_all(services)
    db.commit()

    print("Seeding Appointments...")
    appointments = [
        Appointment(pet_id=1, service_id=2, groomer_name="Thợ Minh", appointment_date="2026-09-05", start_time="09:00", end_time="10:30", status="CONFIRMED", notes="Sấy chế độ êm dịu"),
        Appointment(pet_id=2, service_id=1, groomer_name="Thợ An", appointment_date="2026-09-05", start_time="10:00", end_time="10:45", status="CONFIRMED", notes="Cắt móng cẩn thận"),
        Appointment(pet_id=3, service_id=5, groomer_name="Thợ Minh", appointment_date="2026-09-05", start_time="14:00", end_time="15:00", status="CONFIRMED", notes="Tắm dầu trị nấm"),
        Appointment(pet_id=4, service_id=2, groomer_name="Thợ Minh", appointment_date="2026-09-02", start_time="08:30", end_time="10:00", status="COMPLETED", notes="Đã hoàn thành xuất sắc"),
        Appointment(pet_id=1, service_id=1, groomer_name="Thợ An", appointment_date="2026-08-20", start_time="15:00", end_time="15:45", status="COMPLETED", notes="Lần tắm trước của bé Bơ")
    ]
    db.add_all(appointments)
    db.commit()

    print("Seeding Care Records...")
    care_records = [
        CareRecord(pet_id=4, appointment_id=4, weight_after=11.4, skin_condition="Da bụng sạch, không ve rận", behavior_notes="Ngoan, hợp tác tốt khi chải lông", advice="Nên chải lông hàng ngày tránh bết"),
        CareRecord(pet_id=1, appointment_id=5, weight_after=4.4, skin_condition="Vùng da tai hơi ửng đỏ nhẹ", behavior_notes="Giật chân sau khi sấy gần", advice="Dùng dầu tắm dịu nhẹ không bọt cay")
    ]
    db.add_all(care_records)
    db.commit()

    print("Seeding Vaccination Reminders...")
    vaccines = [
        VaccinationReminder(pet_id=1, vaccine_name="Vắc-xin 7 bệnh Chó (Mũi nhắc hàng năm)", last_date="2025-09-15", next_due_date="2026-09-15", status="PENDING"),
        VaccinationReminder(pet_id=3, vaccine_name="Vắc-xin 4 bệnh Mèo & Dại", last_date="2025-09-20", next_due_date="2026-09-20", status="PENDING"),
        VaccinationReminder(pet_id=2, vaccine_name="Uống thuốc tẩy giun định kỳ", last_date="2026-06-01", next_due_date="2026-09-01", status="PENDING"),
        VaccinationReminder(pet_id=4, vaccine_name="Thuốc nhỏ gáy phòng ve rận Frontline", last_date="2026-08-01", next_due_date="2026-09-01", status="DONE")
    ]
    db.add_all(vaccines)
    db.commit()

    print("Seeding Invoices...")
    inv1 = Invoice(owner_id=3, appointment_id=4, total_amount=320000, discount=20000, final_amount=300000, status="PAID")
    db.add(inv1)
    db.flush()

    item1 = InvoiceItem(invoice_id=inv1.invoice_id, service_id=2, quantity=1, unit_price=320000, subtotal=320000)
    pay1 = Payment(invoice_id=inv1.invoice_id, payment_method="CHUYEN_KHOAN", amount=300000, transaction_code="QR-MB-987654")
    db.add_all([item1, pay1])
    db.commit()

    print("Seeding Service Packages...")
    pkg1 = ServicePackage(package_name="Gói Spa Toàn Diện", description="Combo spa cắt tỉa + dưỡng lông mượt, tiết kiệm hơn mua lẻ.", price=480000)
    pkg1.items = [ServicePackageItem(service_id=2, quantity=1), ServicePackageItem(service_id=3, quantity=1)]
    pkg2 = ServicePackage(package_name="Gói Tắm 4 Lần/Tháng", description="4 lần tắm sấy vệ sinh cơ bản trong tháng.", price=520000)
    pkg2.items = [ServicePackageItem(service_id=1, quantity=4)]
    db.add_all([pkg1, pkg2])
    db.commit()

    print("Seeding Partially-paid Invoice (công nợ demo)...")
    inv2 = Invoice(owner_id=1, appointment_id=5, total_amount=150000, discount=0, final_amount=150000, status="PARTIAL")
    db.add(inv2)
    db.flush()
    db.add_all([InvoiceItem(invoice_id=inv2.invoice_id, service_id=1, quantity=1, unit_price=150000, subtotal=150000),
                Payment(invoice_id=inv2.invoice_id, payment_method="TIEN_MAT", amount=100000)])
    db.commit()

    db.close()
    print("DEMO DATABASE SEEDED SUCCESSFULLY!")

if __name__ == '__main__':
    seed()
