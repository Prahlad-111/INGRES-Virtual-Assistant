
import os
import jwt

from datetime import datetime, timedelta, timezone
from functools import wraps

from dotenv import load_dotenv
from flask import Blueprint, request, jsonify

from database.mongodb import (
    create_secret_id_user,
    login_with_secret_id
)

load_dotenv()

# =========================================================
# AUTH BLUEPRINT
# =========================================================

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)

# =========================================================
# JWT CONFIGURATION
# =========================================================

JWT_SECRET = os.getenv("JWT_SECRET")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set in .env")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 30


# =========================================================
# CREATE JWT TOKEN
# =========================================================

def create_user_token(user_id, name):

    payload = {
        "user_id": user_id,
        "name": name,
        "purpose": "ingres_user",
        "exp": datetime.now(timezone.utc)
        + timedelta(days=JWT_EXPIRATION_DAYS)
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )


# =========================================================
# CREATE NEW ACCOUNT
# =========================================================

@auth_bp.route("/register", methods=["POST"])
def register():

    try:

        data = request.get_json(silent=True) or {}

        name = str(data.get("name", "")).strip()

        if not name:
            return jsonify({
                "success": False,
                "message": "Please enter your name."
            }), 400

        if len(name) > 100:
            return jsonify({
                "success": False,
                "message": "Name must not exceed 100 characters."
            }), 400

        account = create_secret_id_user(name)

        if not account:
            return jsonify({
                "success": False,
                "message": "Unable to create account."
            }), 500

        token = create_user_token(
            account["user_id"],
            account["name"]
        )

        return jsonify({
            "success": True,
            "message": "Your INGRES account is ready!",
            "token": token,
            "user": {
                "id": account["user_id"],
                "name": account["name"]
            },
            "secret_id": account["secret_id"]
        }), 201

    except Exception as error:

        print("[SECRET ID REGISTER ERROR]", error)

        return jsonify({
            "success": False,
            "message": "Account creation failed."
        }), 500


# =========================================================
# LOGIN USING NAME AND SECRET ID
# =========================================================

@auth_bp.route("/login", methods=["POST"])
def login():

    try:

        data = request.get_json(silent=True) or {}

        name = str(data.get("name", "")).strip()

        secret_id = str(
            data.get("secret_id", "")
        ).strip()

        if not name or not secret_id:
            return jsonify({
                "success": False,
                "message": "Name and Secret ID are required."
            }), 400

        user = login_with_secret_id(
            name,
            secret_id
        )

        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid name or Secret ID."
            }), 401

        token = create_user_token(
            user["user_id"],
            user["name"]
        )

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "token": token,
            "user": {
                "id": user["user_id"],
                "name": user["name"]
            }
        }), 200

    except Exception as error:

        print("[SECRET ID LOGIN ERROR]", error)

        return jsonify({
            "success": False,
            "message": "Login failed."
        }), 500


# =========================================================
# JWT AUTHENTICATION
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
                "message": "Authentication required."
            }), 401

        token = auth_header.split(" ", 1)[1].strip()

        try:

            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM]
            )

            if payload.get("purpose") != "ingres_user":
                return jsonify({
                    "success": False,
                    "message": "Invalid authentication token."
                }), 401

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
                "message": "Session expired. Please log in again."
            }), 401

        except jwt.InvalidTokenError:

            return jsonify({
                "success": False,
                "message": "Invalid authentication token."
            }), 401

        return function(*args, **kwargs)

    return decorated


# =========================================================
# TEMPORARY VISITOR COMPATIBILITY
# REMOVE AFTER api/routes.py IS UPDATED
# =========================================================

import uuid


def create_visitor_token():

    visitor_id = str(uuid.uuid4())

    token = jwt.encode(
        {
            "visitor_id": visitor_id,
            "purpose": "anonymous_visitor",
            "exp": datetime.now(timezone.utc)
            + timedelta(days=365)
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
            "X-Visitor-Token", ""
        ).strip()

        if not token:
            return jsonify({
                "success": False,
                "message": "Authentication required."
            }), 401

        try:

            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM]
            )

            if payload.get("purpose") != "anonymous_visitor":
                return jsonify({
                    "success": False,
                    "message": "Invalid token."
                }), 401

            request.visitor_id = payload.get("visitor_id")

        except jwt.InvalidTokenError:

            return jsonify({
                "success": False,
                "message": "Invalid visitor token."
            }), 401

        return function(*args, **kwargs)

    return decorated
