import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings


def generate_link(reset_token: str) -> str:
    return f"{settings.frontend_url}/reset-password?token={reset_token}"


def send_password_reset_email(to_email: str, reset_token: str):
    message = EmailMessage()

    message["Subject"] = "Password Reset Request"
    message["From"] = settings.smtp_from_email
    message["To"] = to_email

    message.set_content(
        f"""
    Hello, 

    You requested to reset your password.

    Your password reset token is: 

    {generate_link(reset_token)}

    This token will expire in 15 minutes.

    if you did not request this, please ignore this email.
    
    """
    )

    with smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
        timeout=10,
    ) as smtp:
        smtp.starttls()
        smtp.login(
            settings.smtp_username,
            settings.smtp_password,
        )
        smtp.send_message(message)


def send_auction_email(to_email: str, subject: str, body: str) -> None:
    message = EmailMessage()

    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
        timeout=20,
    ) as smtp:
        smtp.ehlo()
        smtp.starttls(context=ssl.create_default_context())
        smtp.ehlo()

        smtp.login(settings.smtp_username, settings.smtp_password)

        smtp.send_message(message)
