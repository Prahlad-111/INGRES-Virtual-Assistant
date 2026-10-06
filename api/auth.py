import os
import re
import hmac
import hashlib
import secrets

from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, current_app
from flask_mail import Message

from database.mongodb import (
    get_user_by_email,
    verify_password,
    save_pending_registration,
    get_pending_registration,
    increment_pending_otp_attempts,
    delete_pending_registration,
    create_verified_user_from_pending,
    pending_registrations_collection,
    password_resets_collection,
    update_user_password,
)

load_dotenv()

# =========================================================
# AUTH BLUEPRINT
# =========================================================

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# =========================================================
# CONFIGURATION
# =========================================================

JWT_SECRET = os.getenv("JWT_SECRET")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set in the .env file.")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

OTP_EXPIRATION_MINUTES = 10
OTP_RESEND_SECONDS = 60
OTP_MAX_ATTEMPTS = 5

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$"
)

BLOCKED_EMAIL_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "test.com",
    "demo.com",
    "mailinator.com",
    "tempmail.com",
    "10minutemail.com",
    "guerrillamail.com",
    "yopmail.com",
}


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def make_otp_hash(email, otp):
    """Hash OTP before storing it in MongoDB."""
    value = f"{email}:{otp}:{JWT_SECRET}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def generate_otp():
    """Generate a random six-digit OTP."""
    return f"{secrets.randbelow(1_000_000):06d}"


def valid_email(email):
    """Validate email format and reject blocked domains."""
    if not EMAIL_PATTERN.fullmatch(email):
        return False

    domain = email.rsplit("@", 1)[1].lower()
    return domain not in BLOCKED_EMAIL_DOMAINS


def normalize_datetime(value):
    """Normalize MongoDB datetime values to UTC."""
    if value and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value


def send_email(subject, email, body):
    """Send email through the configured Flask-Mail instance."""
    sender = current_app.config.get("MAIL_DEFAULT_SENDER")

    if (
        not current_app.config.get("MAIL_USERNAME")
        or not current_app.config.get("MAIL_PASSWORD")
        or not sender
    ):
        raise RuntimeError(
            "Gmail SMTP configuration is incomplete."
        )

    mail = current_app.extensions.get("mail")

    if mail is None:
        raise RuntimeError(
            "Flask-Mail has not been initialized."
        )

    message = Message(
        subject=subject,
        recipients=[email],
        sender=sender,
        body=body,
    )

    mail.send(message)


def send_otp_email(email, name, otp):
    """Send registration verification OTP."""
    send_email(
        "Verify your INGRES AI account",
        email,
        (
            f"Hello {name},\n\n"
            f"Your INGRES AI email verification code is: {otp}\n\n"
            f"This code expires in "
            f"{OTP_EXPIRATION_MINUTES} minutes.\n"
            "Do not share this code with anyone.\n\n"
            "INGRES AI Virtual Assistant"
        ),
    )


def send_password_reset_email(email, name, otp):
    """Send password-reset OTP."""
    send_email(
        "Reset your INGRES AI password",
        email,
        (
            f"Hello {name},\n\n"
            f"Your INGRES AI password-reset code is: {otp}\n\n"
            f"This code expires in "
            f"{OTP_EXPIRATION_MINUTES} minutes.\n"
            f"You have a maximum of "
            f"{OTP_MAX_ATTEMPTS} attempts.\n\n"
            "If you did not request a password reset, "
            "you can ignore this email.\n\n"
            "INGRES AI Virtual Assistant"
        ),
    )


# =========================================================
# JWT TOKEN DECORATOR
# =========================================================

def token_required(function):

    @wraps(function)
    def decorated(*args, **kwargs):

        auth_header = request.headers.get(
            "Authorization", ""
        )

        if not auth_header.startswith("Bearer "):
            return jsonify({
                "success": False,
                "message": "Authentication token is required."
            }), 401

        token = auth_header.split(" ", 1)[1].strip()

        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
            )

            user_id = payload.get("user_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "Invalid authentication token."
                }), 401

            request.user_id = user_id
            request.user = payload

        except jwt.ExpiredSignatureError:
            return jsonify({
                "success": False,
                "message": (
                    "Your session has expired. Please login again."
                )
            }), 401

        except jwt.InvalidTokenError:
            return jsonify({
                "success": False,
                "message": "Invalid authentication token."
            }), 401

        return function(*args, **kwargs)

    return decorated


# =========================================================
# REGISTER
# =========================================================

@auth_bp.route("/register", methods=["POST"])
def register():

    try:
        data = request.get_json(silent=True) or {}

        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))

        if not name:
            return jsonify({
                "success": False,
                "message": "Name is required."
            }), 400

        if len(name) > 100:
            return jsonify({
                "success": False,
                "message": "Name must not exceed 100 characters."
            }), 400

        if not valid_email(email):
            return jsonify({
                "success": False,
                "message": "Please enter a valid email address."
            }), 400

        if len(password) < 6 or len(password) > 72:
            return jsonify({
                "success": False,
                "message": (
                    "Password must contain 6 to 72 characters."
                )
            }), 400

        if get_user_by_email(email):
            return jsonify({
                "success": False,
                "message": (
                    "An account with this email already exists."
                )
            }), 409

        pending = get_pending_registration(email)

        if pending:
            last_sent = normalize_datetime(
                pending.get("last_sent_at")
            )

            if last_sent:
                elapsed = (
                    datetime.now(timezone.utc) - last_sent
                ).total_seconds()

                if elapsed < OTP_RESEND_SECONDS:
                    wait = max(
                        1,
                        int(OTP_RESEND_SECONDS - elapsed),
                    )

                    return jsonify({
                        "success": False,
                        "message": (
                            f"Please wait {wait} seconds "
                            "before requesting another code."
                        )
                    }), 429

        otp = generate_otp()
        now = datetime.now(timezone.utc)

        saved = save_pending_registration(
            name,
            email,
            password,
            make_otp_hash(email, otp),
            now + timedelta(
                minutes=OTP_EXPIRATION_MINUTES
            ),
        )

        if not saved:
            return jsonify({
                "success": False,
                "message": (
                    "Unable to start registration. Please try again."
                )
            }), 500

        try:
            send_otp_email(email, name, otp)

            pending_registrations_collection.update_one(
                {"email": email},
                {"$set": {"last_sent_at": now}},
            )

        except Exception as error:
            print("[REGISTER EMAIL ERROR]", error)
            delete_pending_registration(email)

            return jsonify({
                "success": False,
                "message": (
                    "Could not send the verification email. "
                    "Please check email configuration."
                )
            }), 503

        return jsonify({
            "success": True,
            "message": (
                "Verification code sent. Please check your email. "
                "The code expires in 10 minutes."
            )
        }), 200

    except Exception as error:
        print("[REGISTER ERROR]", error)

        return jsonify({
            "success": False,
            "message": "Server error while starting registration."
        }), 500


# =========================================================
# VERIFY REGISTRATION OTP
# =========================================================

@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():

    try:
        data = request.get_json(silent=True) or {}

        email = str(data.get("email", "")).strip().lower()
        otp = str(data.get("otp", "")).strip()

        # Corrected syntax: closing parenthesis is included.
        if not valid_email(email) or not re.fullmatch(
            r"\d{6}", otp
        ):
            return jsonify({
                "success": False,
                "message": (
                    "Enter a valid email and 6-digit OTP."
                )
            }), 400

        pending = get_pending_registration(email)

        if not pending:
            return jsonify({
                "success": False,
                "message": (
                    "No pending registration found. "
                    "Please register again."
                )
            }), 404

        if int(pending.get("attempts", 0)) >= OTP_MAX_ATTEMPTS:
            delete_pending_registration(email)

            return jsonify({
                "success": False,
                "message": (
                    "Too many incorrect attempts. "
                    "Please register again."
                )
            }), 429

        expires_at = normalize_datetime(
            pending.get("expires_at")
        )

        if (
            not expires_at
            or datetime.now(timezone.utc) > expires_at
        ):
            delete_pending_registration(email)

            return jsonify({
                "success": False,
                "message": "OTP expired. Please register again."
            }), 400

        expected = pending.get("otp_hash", "")
        supplied = make_otp_hash(email, otp)

        if not hmac.compare_digest(expected, supplied):
            increment_pending_otp_attempts(email)

            return jsonify({
                "success": False,
                "message": "Incorrect OTP. Please try again."
            }), 400

        created = create_verified_user_from_pending(email)

        if not created:
            return jsonify({
                "success": False,
                "message": (
                    "Unable to complete registration. "
                    "Please try again."
                )
            }), 500

        delete_pending_registration(email)

        return jsonify({
            "success": True,
            "message": (
                "Email verified. Your account has been created. "
                "You can now log in."
            )
        }), 200

    except Exception as error:
        print("[VERIFY OTP ERROR]", error)

        return jsonify({
            "success": False,
            "message": "Server error while verifying OTP."
        }), 500


# =========================================================
# RESEND REGISTRATION OTP
# =========================================================

@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():

    try:
        data = request.get_json(silent=True) or {}

        email = str(data.get("email", "")).strip().lower()

        if not valid_email(email):
            return jsonify({
                "success": False,
                "message": "Enter a valid email address."
            }), 400

        pending = get_pending_registration(email)

        if not pending:
            return jsonify({
                "success": False,
                "message": (
                    "No pending registration found. "
                    "Please register again."
                )
            }), 404

        last_sent = normalize_datetime(
            pending.get("last_sent_at")
        )

        if last_sent:
            elapsed = (
                datetime.now(timezone.utc) - last_sent
            ).total_seconds()

            if elapsed < OTP_RESEND_SECONDS:
                wait = max(
                    1,
                    int(OTP_RESEND_SECONDS - elapsed),
                )

                return jsonify({
                    "success": False,
                    "message": (
                        f"Please wait {wait} seconds "
                        "before requesting another code."
                    )
                }), 429

        otp = generate_otp()
        now = datetime.now(timezone.utc)

        result = pending_registrations_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "otp_hash": make_otp_hash(email, otp),
                    "expires_at": (
                        now + timedelta(
                            minutes=OTP_EXPIRATION_MINUTES
                        )
                    ),
                    "attempts": 0,
                    "last_sent_at": now,
                }
            },
        )

        if result.matched_count == 0:
            return jsonify({
                "success": False,
                "message": (
                    "Registration not found. Please register again."
                )
            }), 404

        try:
            send_otp_email(
                email,
                pending.get("name", "there"),
                otp,
            )

        except Exception as error:
            print("[RESEND OTP EMAIL ERROR]", error)

            return jsonify({
                "success": False,
                "message": (
                    "Could not send OTP email. Please try again later."
                )
            }), 503

        return jsonify({
            "success": True,
            "message": "A new verification code has been sent."
        }), 200

    except Exception as error:
        print("[RESEND OTP ERROR]", error)

        return jsonify({
            "success": False,
            "message": "Server error while resending OTP."
        }), 500


# =========================================================
# LOGIN
# =========================================================

@auth_bp.route("/login", methods=["POST"])
def login():

    try:
        data = request.get_json(silent=True) or {}

        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))

        if not email or not password:
            return jsonify({
                "success": False,
                "message": "Email and password are required."
            }), 400

        user = get_user_by_email(email)

        if not user or not verify_password(
            password,
            user.get("password_hash", ""),
        ):
            return jsonify({
                "success": False,
                "message": "Invalid email or password."
            }), 401

        if user.get("email_verified") is False:
            return jsonify({
                "success": False,
                "message": (
                    "Please verify your email before logging in."
                )
            }), 403

        user_id = str(user.get("_id", user.get("id", "")))

        token = jwt.encode(
            {
                "user_id": user_id,
                "email": email,
                "exp": (
                    datetime.now(timezone.utc)
                    + timedelta(hours=JWT_EXPIRATION_HOURS)
                ),
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "token": token,
            "user": {
                "id": user_id,
                "name": user.get("name", ""),
                "email": email,
            },
        }), 200

    except Exception as error:
        print("[LOGIN ERROR]", error)

        return jsonify({
            "success": False,
            "message": "Server error during login."
        }), 500


# =========================================================
# FORGOT PASSWORD: SEND RESET OTP
# =========================================================

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():

    generic_response = {
        "success": True,
        "message": (
            "If a verified account exists for that email, "
            "a password-reset code will be sent."
        ),
    }

    try:
        data = request.get_json(silent=True) or {}

        email = str(data.get("email", "")).strip().lower()

        # Return a generic response to avoid revealing accounts.
        if not valid_email(email):
            return jsonify(generic_response), 200

        user = get_user_by_email(email)

        if not user or user.get("email_verified") is False:
            return jsonify(generic_response), 200

        existing = password_resets_collection.find_one(
            {"email": email}
        )

        if existing:
            last_sent = normalize_datetime(
                existing.get("last_sent_at")
            )

            if last_sent:
                elapsed = (
                    datetime.now(timezone.utc) - last_sent
                ).total_seconds()

                if elapsed < OTP_RESEND_SECONDS:
                    return jsonify(generic_response), 200

        otp = generate_otp()
        now = datetime.now(timezone.utc)

        password_resets_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "otp_hash": make_otp_hash(email, otp),
                    "expires_at": (
                        now + timedelta(
                            minutes=OTP_EXPIRATION_MINUTES
                        )
                    ),
                    "attempts": 0,
                    "last_sent_at": now,
                }
            },
            upsert=True,
        )

        try:
            send_password_reset_email(
                email,
                user.get("name", "there"),
                otp,
            )

        except Exception as error:
            print("[PASSWORD RESET EMAIL ERROR]", error)

            password_resets_collection.delete_one(
                {"email": email}
            )

        return jsonify(generic_response), 200

    except Exception as error:
        print("[FORGOT PASSWORD ERROR]", error)

        return jsonify({
            "success": False,
            "message": (
                "Unable to process password reset right now."
            )
        }), 500


# =========================================================
# RESET PASSWORD: VERIFY OTP AND UPDATE PASSWORD
# =========================================================

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():

    try:
        data = request.get_json(silent=True) or {}

        email = str(data.get("email", "")).strip().lower()
        otp = str(data.get("otp", "")).strip()
        new_password = str(data.get("new_password", ""))

        # Validate email and six-digit OTP.
        if not valid_email(email) or not re.fullmatch(
            r"\d{6}", otp
        ):
            return jsonify({
                "success": False,
                "message": (
                    "Enter a valid email and 6-digit OTP."
                )
            }), 400

        if len(new_password) < 6 or len(new_password) > 72:
            return jsonify({
                "success": False,
                "message": (
                    "New password must contain 6 to 72 characters."
                )
            }), 400

        record = password_resets_collection.find_one(
            {"email": email}
        )

        if not record:
            return jsonify({
                "success": False,
                "message": (
                    "Reset code is invalid or expired. "
                    "Request a new code."
                )
            }), 400

        if int(record.get("attempts", 0)) >= OTP_MAX_ATTEMPTS:
            password_resets_collection.delete_one(
                {"email": email}
            )

            return jsonify({
                "success": False,
                "message": (
                    "Too many incorrect attempts. "
                    "Request a new code."
                )
            }), 429

        expires_at = normalize_datetime(
            record.get("expires_at")
        )

        if (
            not expires_at
            or datetime.now(timezone.utc) > expires_at
        ):
            password_resets_collection.delete_one(
                {"email": email}
            )

            return jsonify({
                "success": False,
                "message": (
                    "Reset code expired. Request a new code."
                )
            }), 400

        expected_hash = record.get("otp_hash", "")
        supplied_hash = make_otp_hash(email, otp)

        if not hmac.compare_digest(
            expected_hash,
            supplied_hash,
        ):
            password_resets_collection.update_one(
                {"email": email},
                {"$inc": {"attempts": 1}},
            )

            return jsonify({
                "success": False,
                "message": "Incorrect reset code."
            }), 400

        user = get_user_by_email(email)

        if not user or user.get("email_verified") is False:
            password_resets_collection.delete_one(
                {"email": email}
            )

            return jsonify({
                "success": False,
                "message": (
                    "Unable to reset password for this account."
                )
            }), 400

        updated = update_user_password(
            email,
            new_password,
        )

        if not updated:
            return jsonify({
                "success": False,
                "message": (
                    "Password could not be updated. Please try again."
                )
            }), 500

        password_resets_collection.delete_one(
            {"email": email}
        )

        return jsonify({
            "success": True,
            "message": (
                "Password reset successful. "
                "Please log in with your new password."
            )
        }), 200

    except Exception as error:
        print("[RESET PASSWORD ERROR]", error)

        return jsonify({
            "success": False,
            "message": (
                "Server error while resetting password."
            )
        }), 500