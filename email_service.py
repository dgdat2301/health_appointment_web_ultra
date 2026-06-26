import os
import smtplib
from pathlib import Path
from email.message import EmailMessage
from dotenv import load_dotenv


class EmailService:
    def __init__(self):
        env_path = Path(__file__).parent / ".env"
        load_dotenv(dotenv_path=env_path)

        self.sender_email = os.getenv("EMAIL_SENDER")
        self.app_password = os.getenv("EMAIL_APP_PASSWORD")

    def send_reminder(self, patient_email, patient_name, doctor_name, clinic_name, appointment_time):
        subject = "Nhắc lịch khám sức khỏe"

        body = f"""
Xin chào {patient_name},

Bạn đã đặt lịch khám sức khỏe thành công.

THÔNG TIN LỊCH KHÁM
- Bệnh nhân: {patient_name}
- Bác sĩ: {doctor_name}
- Phòng khám: {clinic_name}
- Thời gian: {appointment_time}

Vui lòng đến đúng giờ và mang theo giấy tờ cần thiết.

Trân trọng,
Hệ thống Health Booking Ultra
"""

        if not self.sender_email or not self.app_password:
            return False, "Chưa cấu hình EMAIL_SENDER hoặc EMAIL_APP_PASSWORD trong file .env"

        try:
            msg = EmailMessage()
            msg["From"] = self.sender_email
            msg["To"] = patient_email
            msg["Subject"] = subject
            msg.set_content(body)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=8) as smtp:
                smtp.login(self.sender_email, self.app_password)
                smtp.send_message(msg)

            return True, f"Đã gửi email nhắc lịch thật đến {patient_email}"

        except Exception as error:
            return False, f"Gửi email thất bại: {error}"
