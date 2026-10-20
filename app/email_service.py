import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.environ["SMTP_PORT"])
SMTP_USERNAME = os.environ["SMTP_USERNAME"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
SMTP_FROM_EMAIL = os.environ["SMTP_FROM_EMAIL"]


def send_password_reset_email(to_email: str, reset_token: str):
    message = EmailMessage()

    message["Subject"] = "Password Reset Request"
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = to_email

    message.set_content(
        f"""
    Hello, 

    You requested to reset your password.

    Your password reset token is: 

    {reset_token}

    This token will expire in 15 minutes.

    if you did not request this, please ignore this email.
    
    """
    )

    with smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT,
        timeout=10,
    ) as smtp:
        smtp.starttls()
        smtp.login(
            SMTP_USERNAME,
            SMTP_PASSWORD,
        )
        smtp.send_message(message)
