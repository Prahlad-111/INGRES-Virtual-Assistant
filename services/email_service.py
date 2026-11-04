import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()


def send_otp_email(receiver_email, otp, purpose="verification"):
    """Send OTP emails using Brevo SMTP."""

    smtp_host = os.getenv("BREVO_SMTP_HOST")
    smtp_port = int(os.getenv("BREVO_SMTP_PORT", "587"))
    smtp_login = os.getenv("BREVO_SMTP_LOGIN")
    smtp_key = os.getenv("BREVO_SMTP_KEY")
    sender_email = os.getenv("BREVO_SENDER_EMAIL")
    sender_name = os.getenv("BREVO_SENDER_NAME", "INGRES AI")

    if not all([smtp_host, smtp_login, smtp_key, sender_email]):
        raise RuntimeError("Brevo SMTP configuration is incomplete.")

    # Select email subject and heading
    if purpose == "login":
        subject = "INGRES AI - Login OTP"
        heading = "Login Verification"
        description = "Your INGRES AI login verification code is:"

    elif purpose in ("reset", "password_reset"):
        subject = "INGRES AI - Password Reset OTP"
        heading = "Password Reset Verification"
        description = "Your INGRES AI password reset code is:"

    else:
        subject = "INGRES AI - Email Verification OTP"
        heading = "Verify Your Email"
        description = "Your INGRES AI email verification code is:"

    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = formataddr((sender_name, sender_email))
    message["To"] = receiver_email

    message.set_content(
        f"""Hello,

{description}

{otp}

This OTP is valid for 5 minutes.

If you did not request this code, please ignore this email.

Regards,
INGRES AI Team
"""
    )

    message.add_alternative(
        f"""
        <html>
        <body>
            <h2>{heading}</h2>
            <p>{description}</p>
            <h1 style="letter-spacing: 5px;">{otp}</h1>
            <p>This OTP is valid for 5 minutes.</p>
            <p>If you did not request this code, ignore this email.</p>
            <br>
            <p>Regards,<br>INGRES AI Team</p>
        </body>
        </html>
        """,
        subtype="html"
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_login, smtp_key)
            server.send_message(message)

        print(f"[BREVO] {purpose} OTP email sent successfully.")

        return True

    except (smtplib.SMTPException, OSError) as error:
        print("[BREVO EMAIL ERROR]:", type(error).__name__)
        raise RuntimeError("Unable to send OTP email.") from error
