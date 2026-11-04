import os
import re
import jwt
import uuid
import hmac
import hashlib
import secrets

try:
    import dns.resolver
except ImportError:
    dns = None

from datetime import datetime, timedelta, timezone
from functools import wraps

from dotenv import load_dotenv
from flask import Blueprint, request, jsonify

from database.mongodb import (
    get_user_by_email,
    get_user_by_id,
    verify_password,
    save_pending_registration,
    get_pending_registration,
    increment_pending_otp_attempts,
    delete_pending_registration,
    create_verified_user_from_pending,
    save_email_otp,
    get_email_otp,
    increment_email_otp_attempts,
    delete_email_otp,
    update_user_password
)

from services.email_service import send_otp_email

load_dotenv()

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

JWT_SECRET = os.getenv("JWT_SECRET")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set in .env")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 30
VISITOR_EXPIRATION_DAYS = 365
OTP_EXPIRATION_MINUTES = 5
MAX_OTP_ATTEMPTS = 5


# =========================================================
# COMMON HELPERS
# =========================================================

def normalize_email(email):
    return str(email or "").strip().lower()


def is_valid_email(email):
    if not email or len(email) > 254:
        return False

    return bool(
        re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email
        )
    )


def email_domain_can_receive_mail(email):
    """
    Checks whether the domain has MX records.

    This does not prove that the individual mailbox exists.
    """

    if dns is None:
        raise RuntimeError("dnspython is not installed")

    domain = email.rsplit("@", 1)[1].lower()

    blocked_domains = {
        "example.com",
        "example.org",
        "example.net",
        "example.test",
        "domain.test",
        "test.com",
        "localhost"
    }

    if (
        domain in blocked_domains
        or domain.endswith((
            ".test",
            ".invalid",
            ".localhost",
            ".example"
        ))
    ):
        return False

    try:
        answers = dns.resolver.resolve(
            domain,
            "MX",
            lifetime=4
        )

        return len(answers) > 0

    except (
        dns.resolver.NXDOMAIN,
        dns.resolver.NoAnswer,
        dns.resolver.NoNameservers
    ):
        return False

    except dns.exception.Timeout as error:
        raise TimeoutError(
            "Email domain lookup timed out"
        ) from error


def generate_otp():
    return f"{secrets.randbelow(1000000):06d}"


def is_valid_otp(otp):
    return bool(
        re.fullmatch(r"\d{6}", str(otp or ""))
    )


def hash_otp(otp):
    return hmac.new(
        JWT_SECRET.encode("utf-8"),
        str(otp).encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def verify_otp(otp, stored_hash):
    if not otp or not stored_hash:
        return False

    return hmac.compare_digest(
        hash_otp(otp),
        str(stored_hash)
    )


def get_expiry():
    return datetime.now(timezone.utc) + timedelta(
        minutes=OTP_EXPIRATION_MINUTES
    )


def otp_is_expired(record):
    if not record:
        return True

    expires_at = record.get("expires_at")

    if not isinstance(expires_at, datetime):
        return True

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc
        )

    return datetime.now(timezone.utc) >= expires_at


def get_user_id(user):
    if not user:
        return None

    user_id = (
        user.get("user_id")
        or user.get("_id")
        or user.get("id")
    )

    return str(user_id) if user_id else None


def create_user_token(user_id, name):
    payload = {
        "user_id": str(user_id),
        "name": name,
        "purpose": "ingres_user",
        "iat": datetime.now(timezone.utc),
        "exp": (
            datetime.now(timezone.utc)
            + timedelta(days=JWT_EXPIRATION_DAYS)
        )
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )


def user_response(user):
    return {
        "id": get_user_id(user),
        "name": user.get("name", ""),
        "email": user.get("email", "")
    }


def error_response(message, status_code):
    return jsonify({
        "success": False,
        "message": message
    }), status_code


# =========================================================
# REGISTER - SEND EMAIL VERIFICATION OTP
# =========================================================

@auth_bp.route("/register", methods=["POST"])
def register():

    try:
        data = request.get_json(silent=True) or {}

        name = str(data.get("name", "")).strip()
        email = normalize_email(data.get("email"))
        password = str(data.get("password", ""))
        confirm_password = str(
            data.get("confirm_password", "")
        )

        if (
            not name
            or not email
            or not password
            or not confirm_password
        ):
            return error_response(
                "Name, email, password and confirm password are required.",
                400
            )

        if len(name) > 100:
            return error_response(
                "Name must not exceed 100 characters.",
                400
            )

        if not is_valid_email(email):
            return error_response(
                "Please enter a valid email address to create an account.",
                400
            )

        # Check email domain before generating OTP.
        try:
            if not email_domain_can_receive_mail(email):
                return error_response(
                    "Please enter a valid email address to create an account.",
                    400
                )

        except RuntimeError:
            return error_response(
                "Email verification is not configured. Install dnspython.",
                503
            )

        except TimeoutError:
            return error_response(
                "Unable to verify this email domain right now. Please try again.",
                503
            )

        if password != confirm_password:
            return error_response(
                "Passwords do not match.",
                400
            )

        if len(password) < 8:
            return error_response(
                "Password must contain at least 8 characters.",
                400
            )

        if len(password.encode("utf-8")) > 72:
            return error_response(
                "Password is too long.",
                400
            )

        existing_user = get_user_by_email(email)

        if existing_user:
            return error_response(
                "An account with this email already exists.",
                409
            )

        otp = generate_otp()

        saved = save_pending_registration(
            name,
            email,
            password,
            hash_otp(otp),
            get_expiry()
        )

        if not saved:
            return error_response(
                "Unable to start registration. Please try again.",
                500
            )

        try:
            send_otp_email(
                email,
                otp,
                purpose="verification"
            )

        except Exception:
            delete_pending_registration(email)
            raise

        return jsonify({
            "success": True,
            "message": "Verification OTP sent to your email.",
            "email": email
        }), 200

    except Exception as error:
        print("[REGISTER ERROR]", type(error).__name__)

        return error_response(
            "Registration failed. Please try again.",
            500
        )


# =========================================================
# VERIFY REGISTRATION OTP
# =========================================================

@auth_bp.route("/verify-registration", methods=["POST"])
def verify_registration():

    try:
        data = request.get_json(silent=True) or {}

        email = normalize_email(data.get("email"))
        otp = str(data.get("otp", "")).strip()

        if not is_valid_email(email) or not is_valid_otp(otp):
            return error_response(
                "Enter a valid email and 6-digit OTP.",
                400
            )

        pending = get_pending_registration(email)

        if not pending:
            return error_response(
                "Registration request not found or expired.",
                404
            )

        if otp_is_expired(pending):
            delete_pending_registration(email)

            return error_response(
                "OTP expired. Please register again.",
                400
            )

        if pending.get("attempts", 0) >= MAX_OTP_ATTEMPTS:
            delete_pending_registration(email)

            return error_response(
                "Too many incorrect attempts. Please register again.",
                429
            )

        if not verify_otp(
            otp,
            pending.get("otp_hash")
        ):
            increment_pending_otp_attempts(email)

            return error_response(
                "Incorrect OTP.",
                400
            )

        user = create_verified_user_from_pending(email)

        if not user:
            return error_response(
                "Unable to complete registration. Please try again.",
                500
            )

        user_id = get_user_id(user)

        if not user_id:
            return error_response(
                "Account created, but login could not be started.",
                500
            )

        token = create_user_token(
            user_id,
            user.get("name", "")
        )

        return jsonify({
            "success": True,
            "message": "Email verified. Your account is ready!",
            "token": token,
            "user": user_response(user)
        }), 201

    except Exception as error:
        print(
            "[REGISTRATION VERIFICATION ERROR]",
            type(error).__name__
        )

        return error_response(
            "Unable to verify your email.",
            500
        )


# =========================================================
# LOGIN - CHECK PASSWORD AND SEND OTP
# =========================================================

@auth_bp.route("/login", methods=["POST"])
def login():

    try:
        data = request.get_json(silent=True) or {}

        email = normalize_email(data.get("email"))
        password = str(data.get("password", ""))

        if not is_valid_email(email) or not password:
            return error_response(
                "Enter a valid email and password.",
                400
            )

        user = get_user_by_email(email)

        if not user or not user.get("email_verified", False):
            return error_response(
                "Invalid email or password.",
                401
            )

        if not verify_password(
            password,
            user.get("password_hash", "")
        ):
            return error_response(
                "Invalid email or password.",
                401
            )

        otp = generate_otp()

        saved = save_email_otp(
            email,
            "login",
            hash_otp(otp),
            get_expiry()
        )

        if not saved:
            return error_response(
                "Unable to generate login OTP.",
                500
            )

        try:
            send_otp_email(
                email,
                otp,
                purpose="login"
            )

        except Exception:
            delete_email_otp(email, "login")
            raise

        return jsonify({
            "success": True,
            "message": "Login OTP sent to your email.",
            "email": email
        }), 200

    except Exception as error:
        print("[LOGIN ERROR]", type(error).__name__)

        return error_response(
            "Login failed. Please try again.",
            500
        )


# =========================================================
# VERIFY LOGIN OTP
# =========================================================

@auth_bp.route("/verify-login", methods=["POST"])
def verify_login():

    try:
        data = request.get_json(silent=True) or {}

        email = normalize_email(data.get("email"))
        otp = str(data.get("otp", "")).strip()

        if not is_valid_email(email) or not is_valid_otp(otp):
            return error_response(
                "Enter a valid email and 6-digit OTP.",
                400
            )

        record = get_email_otp(email, "login")

        if not record:
            return error_response(
                "Login OTP not found or expired.",
                404
            )

        if otp_is_expired(record):
            delete_email_otp(email, "login")

            return error_response(
                "OTP expired. Please log in again.",
                400
            )

        if record.get("attempts", 0) >= MAX_OTP_ATTEMPTS:
            delete_email_otp(email, "login")

            return error_response(
                "Too many incorrect attempts. Please log in again.",
                429
            )

        if not verify_otp(
            otp,
            record.get("otp_hash")
        ):
            increment_email_otp_attempts(email, "login")

            return error_response(
                "Incorrect OTP.",
                400
            )

        user = get_user_by_email(email)

        if not user or not user.get("email_verified", False):
            delete_email_otp(email, "login")

            return error_response(
                "Verified account not found.",
                404
            )

        user_id = get_user_id(user)

        if not user_id:
            return error_response(
                "Unable to start your session.",
                500
            )

        delete_email_otp(email, "login")

        token = create_user_token(
            user_id,
            user.get("name", "")
        )

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "token": token,
            "user": user_response(user)
        }), 200

    except Exception as error:
        print("[LOGIN OTP ERROR]", type(error).__name__)

        return error_response(
            "Unable to verify login OTP.",
            500
        )


# =========================================================
# FORGOT PASSWORD - SEND RESET OTP
# =========================================================

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():

    try:
        data = request.get_json(silent=True) or {}

        email = normalize_email(data.get("email"))

        if not is_valid_email(email):
            return error_response(
                "Please enter a valid email address.",
                400
            )

        user = get_user_by_email(email)

        # Do not reveal whether an account exists.
        if user and user.get("email_verified", False):

            otp = generate_otp()

            saved = save_email_otp(
                email,
                "password_reset",
                hash_otp(otp),
                get_expiry()
            )

            if not saved:
                raise RuntimeError(
                    "Unable to save password reset OTP."
                )

            try:
                send_otp_email(
                    email,
                    otp,
                    purpose="password_reset"
                )

            except Exception:
                delete_email_otp(email, "password_reset")
                raise

        return jsonify({
            "success": True,
            "message": (
                "If a verified account exists for this email, "
                "a password reset OTP has been sent."
            )
        }), 200

    except Exception as error:
        print("[FORGOT PASSWORD ERROR]", type(error).__name__)

        return error_response(
            "Unable to process your request. Please try again.",
            500
        )


# =========================================================
# RESET PASSWORD
# =========================================================

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():

    try:
        data = request.get_json(silent=True) or {}

        email = normalize_email(data.get("email"))
        otp = str(data.get("otp", "")).strip()
        new_password = str(data.get("new_password", ""))

        if (
            not is_valid_email(email)
            or not is_valid_otp(otp)
            or not new_password
        ):
            return error_response(
                "Enter a valid email, 6-digit OTP and new password.",
                400
            )

        if len(new_password) < 8:
            return error_response(
                "New password must contain at least 8 characters.",
                400
            )

        if len(new_password.encode("utf-8")) > 72:
            return error_response(
                "Password is too long.",
                400
            )

        record = get_email_otp(
            email,
            "password_reset"
        )

        if not record:
            return error_response(
                "Reset OTP not found or expired.",
                404
            )

        if otp_is_expired(record):
            delete_email_otp(email, "password_reset")

            return error_response(
                "OTP expired. Please request another OTP.",
                400
            )

        if record.get("attempts", 0) >= MAX_OTP_ATTEMPTS:
            delete_email_otp(email, "password_reset")

            return error_response(
                "Too many incorrect attempts. Request another OTP.",
                429
            )

        if not verify_otp(
            otp,
            record.get("otp_hash")
        ):
            increment_email_otp_attempts(
                email,
                "password_reset"
            )

            return error_response(
                "Incorrect OTP.",
                400
            )

        updated = update_user_password(
            email,
            new_password
        )

        if not updated:
            return error_response(
                "Unable to update password.",
                400
            )

        delete_email_otp(email, "password_reset")

        return jsonify({
            "success": True,
            "message": (
                "Password reset successful. "
                "Please log in with your new password."
            )
        }), 200

    except Exception as error:
        print("[RESET PASSWORD ERROR]", type(error).__name__)

        return error_response(
            "Password reset failed. Please try again.",
            500
        )


# =========================================================
# JWT AUTHENTICATION
# =========================================================

def token_required(function):

    @wraps(function)
    def decorated(*args, **kwargs):

        auth_header = request.headers.get(
            "Authorization",
            ""
        )

        if not auth_header.startswith("Bearer "):
            return error_response(
                "Authentication required.",
                401
            )

        token = auth_header.split(" ", 1)[1].strip()

        if not token:
            return error_response(
                "Authentication required.",
                401
            )

        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM]
            )

            if payload.get("purpose") != "ingres_user":
                return error_response(
                    "Invalid authentication token.",
                    401
                )

            user_id = payload.get("user_id")

            if not user_id:
                return error_response(
                    "Invalid authentication token.",
                    401
                )

            user = get_user_by_id(user_id)

            if not user or not user.get("email_verified", False):
                return error_response(
                    "Account not found or not verified. Please log in again.",
                    401
                )

            request.user_id = user_id
            request.user = payload

        except jwt.ExpiredSignatureError:
            return error_response(
                "Session expired. Please log in again.",
                401
            )

        except jwt.InvalidTokenError:
            return error_response(
                "Invalid authentication token.",
                401
            )

        return function(*args, **kwargs)

    return decorated


# =========================================================
# VISITOR AUTHENTICATION
# =========================================================

def create_visitor_token():

    visitor_id = str(uuid.uuid4())

    token = jwt.encode(
        {
            "visitor_id": visitor_id,
            "purpose": "anonymous_visitor",
            "iat": datetime.now(timezone.utc),
            "exp": (
                datetime.now(timezone.utc)
                + timedelta(days=VISITOR_EXPIRATION_DAYS)
            )
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    return {
        "visitor_id": visitor_id,
        "visitor_token": token
    }


def visitor_token_required(function):

    @wraps(function)
    def decorated(*args, **kwargs):

        token = request.headers.get(
            "X-Visitor-Token",
            ""
        ).strip()

        if not token:
            return error_response(
                "Authentication required.",
                401
            )

        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM]
            )

            if payload.get("purpose") != "anonymous_visitor":
                return error_response(
                    "Invalid visitor token.",
                    401
                )

            visitor_id = payload.get("visitor_id")

            if not visitor_id:
                return error_response(
                    "Invalid visitor token.",
                    401
                )

            request.visitor_id = visitor_id

        except jwt.ExpiredSignatureError:
            return error_response(
                "Visitor session expired.",
                401
            )

        except jwt.InvalidTokenError:
            return error_response(
                "Invalid visitor token.",
                401
            )

        return function(*args, **kwargs)

    return decorated