import os
import requests
from dotenv import load_dotenv

load_dotenv()


def send_otp_email(receiver_email, otp, purpose="verification"):
    """Send OTP emails using Brevo's HTTP API."""

    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("BREVO_SENDER_EMAIL")
    sender_name = os.getenv("BREVO_SENDER_NAME", "INGRES AI")

    if not all([api_key, sender_email]):
        raise RuntimeError("Brevo API configuration is incomplete.")

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

    text_content = f"""Hello,

{description}

{otp}

This OTP is valid for 5 minutes.

If you did not request this code, please ignore this email.

Regards,
INGRES AI Team
"""

    html_content = f"""
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
        """

    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": api_key,
                "accept": "application/json",
                "content-type": "application/json",
            },
            json={
                "sender": {
                    "name": sender_name,
                    "email": sender_email,
                },
                "to": [{"email": receiver_email}],
                "subject": subject,
                "textContent": text_content,
                "htmlContent": html_content,
            },
            timeout=20,
        )
        response.raise_for_status()

        print(f"[BREVO API] {purpose} OTP email sent successfully.")

        return True

    except requests.RequestException as error:
        status_code = (
            error.response.status_code
            if error.response is not None
            else "connection error"
        )
        print("[BREVO API ERROR]:", status_code)
        raise RuntimeError("Unable to send OTP email.") from error
