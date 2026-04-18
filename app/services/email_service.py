import smtplib
from email.message import EmailMessage
from app.core.config import settings


def send_reset_code_email(to_email: str, username: str, code: str) -> bool:
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        return False

    message = EmailMessage()
    message["Subject"] = "Baghchal Password Reset Code"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email
    message.set_content(
        f"Hello {username},\n\n"
        f"Your password reset code is: {code}\n"
        "This code expires in 10 minutes.\n\n"
        "If you did not request this, please ignore this email."
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)

    return True
