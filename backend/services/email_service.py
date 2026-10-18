import os
import smtplib
from email.message import EmailMessage


def send_verification_code(recipient, code):
    host = os.getenv("SMTP_HOST")
    if not host:
        return {"sent": False, "mode": "development", "code": code}
    message = EmailMessage()
    message["Subject"] = "MediBridge AI verification code"
    message["From"] = os.getenv("SMTP_FROM", os.getenv("SMTP_USERNAME", ""))
    message["To"] = recipient
    message.set_content(f"Your MediBridge AI verification code is {code}.")
    with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587"))) as server:
        server.starttls()
        server.login(os.getenv("SMTP_USERNAME", ""), os.getenv("SMTP_PASSWORD", ""))
        server.send_message(message)
    return {"sent": True, "mode": "smtp"}
