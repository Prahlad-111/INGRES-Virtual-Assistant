import os
import bcrypt

from datetime import datetime, timezone
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient, DESCENDING


# =========================================================
# ENVIRONMENT AND MONGODB CONFIGURATION
# =========================================================

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "ingres_ai"

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not configured in .env")

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client[DATABASE_NAME]


# =========================================================
# COLLECTIONS
# =========================================================

users_collection = db["users"]
conversations_collection = db["conversations"]
messages_collection = db["messages"]

pending_registrations_collection = db["pending_registrations"]
email_otps_collection = db["email_otps"]
password_resets_collection = db["password_resets"]


# =========================================================
# DATABASE INDEXES
# =========================================================

try:
    users_collection.create_index(
        [("email", 1)],
        unique=True,
        partialFilterExpression={
            "email": {"$type": "string"}
        },
        name="email_string_unique"
    )

    pending_registrations_collection.create_index(
        "expires_at",
        expireAfterSeconds=0
    )

    email_otps_collection.create_index(
        "expires_at",
        expireAfterSeconds=0
    )

    password_resets_collection.create_index(
        "expires_at",
        expireAfterSeconds=0
    )

    print("[INDEX] MongoDB indexes configured.")

except Exception as error:
    print("[INDEX WARNING]", type(error).__name__)


# =========================================================
# COMMON HELPERS
# =========================================================

def normalize_email(email):
    return str(email or "").strip().lower()


def format_datetime(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    return str(value)


def hash_password(password):
    if not password or len(password) < 8 or len(password) > 72:
        raise ValueError("Password must contain 8-72 characters.")

    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password, password_hash):
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )

    except Exception:
        return False


# =========================================================
# TEST MONGODB CONNECTION
# =========================================================

def test_connection():
    try:
        client.admin.command("ping")

        print("MongoDB connected successfully!")
        print(f"Database: {DATABASE_NAME}")

        return True

    except Exception as error:
        print("MongoDB connection failed!")
        print("Error:", type(error).__name__)

        return False


# =========================================================
# USER ACCOUNT FUNCTIONS
# =========================================================

def create_user(name, email, password):
    """
    Direct account creation is disabled.

    New accounts must be created through:
    save_pending_registration()
    followed by successful OTP verification.
    """

    print(
        "[CREATE USER BLOCKED] "
        "Use email OTP verification to create accounts."
    )

    return None


def get_user_by_email(email):
    return users_collection.find_one({
        "email": normalize_email(email)
    })


def get_user_by_id(user_id):
    try:
        return users_collection.find_one({
            "_id": ObjectId(user_id)
        })

    except Exception:
        return None


def update_user_profile(user_id, name=None, profile_image_url=None):
    try:
        updates = {
            "updated_at": datetime.now(timezone.utc)
        }

        if name is not None:
            name = name.strip()

            if not name or len(name) > 100:
                return False

            updates["name"] = name

        if profile_image_url is not None:
            updates["profile_image_url"] = profile_image_url

        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": updates}
        )

        return result.matched_count == 1

    except Exception as error:
        print("[PROFILE UPDATE ERROR]", type(error).__name__)
        return False


# =========================================================
# REGISTRATION OTP FUNCTIONS
# =========================================================

def save_pending_registration(
    name,
    email,
    password,
    otp_hash,
    expires_at
):
    name = str(name or "").strip()
    email = normalize_email(email)

    if not name or len(name) > 100:
        return False

    if not password or len(password) < 8 or len(password) > 72:
        return False

    # Do not allow duplicate permanent accounts.
    if get_user_by_email(email):
        return False

    try:
        password_hash = hash_password(password)
        now = datetime.now(timezone.utc)

        pending_registrations_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "name": name,
                    "email": email,
                    "password_hash": password_hash,
                    "otp_hash": otp_hash,
                    "expires_at": expires_at,
                    "attempts": 0,
                    "created_at": now,
                    "last_sent_at": now
                }
            },
            upsert=True
        )

        return True

    except Exception as error:
        print("[SAVE REGISTRATION ERROR]", type(error).__name__)
        return False


def get_pending_registration(email):
    return pending_registrations_collection.find_one({
        "email": normalize_email(email)
    })


def increment_pending_otp_attempts(email):
    email = normalize_email(email)

    pending_registrations_collection.update_one(
        {"email": email},
        {"$inc": {"attempts": 1}}
    )

    pending = get_pending_registration(email)

    return pending.get("attempts", 0) if pending else 0


def delete_pending_registration(email):
    result = pending_registrations_collection.delete_one({
        "email": normalize_email(email)
    })

    return result.deleted_count > 0


def create_verified_user_from_pending(email):
    """
    Create a permanent verified account after successful OTP
    verification.

    Returns the complete user dictionary.
    """

    email = normalize_email(email)

    pending = get_pending_registration(email)

    if not pending:
        return None

    # Prevent duplicate accounts.
    if get_user_by_email(email):
        delete_pending_registration(email)
        return None

    now = datetime.now(timezone.utc)

    user_document = {
        "name": pending["name"],
        "email": email,
        "password_hash": pending["password_hash"],
        "email_verified": True,
        "email_verified_at": now,
        "created_at": now,
        "updated_at": now
    }

    try:
        result = users_collection.insert_one(user_document)

        user_document["_id"] = result.inserted_id

        # Delete pending registration after account creation.
        delete_pending_registration(email)

        return user_document

    except Exception as error:
        print("[CREATE VERIFIED USER ERROR]", type(error).__name__)
        return None


# =========================================================
# LOGIN AND PASSWORD RESET OTP FUNCTIONS
# =========================================================

def save_email_otp(email, purpose, otp_hash, expires_at):
    """
    Save login or password-reset OTP.

    Correct argument order:
    email, purpose, otp_hash, expires_at
    """

    email = normalize_email(email)

    allowed_purposes = (
        "login",
        "password_reset"
    )

    if purpose not in allowed_purposes:
        print("[SAVE EMAIL OTP ERROR] Invalid OTP purpose")
        return False

    try:
        now = datetime.now(timezone.utc)

        email_otps_collection.update_one(
            {
                "email": email,
                "purpose": purpose
            },
            {
                "$set": {
                    "email": email,
                    "otp_hash": otp_hash,
                    "purpose": purpose,
                    "expires_at": expires_at,
                    "attempts": 0,
                    "created_at": now
                }
            },
            upsert=True
        )

        print(f"[OTP] {purpose} OTP saved successfully.")

        return True

    except Exception as error:
        print("[SAVE EMAIL OTP ERROR]", type(error).__name__)
        return False


def get_email_otp(email, purpose):
    return email_otps_collection.find_one({
        "email": normalize_email(email),
        "purpose": purpose
    })


def increment_email_otp_attempts(email, purpose):
    email = normalize_email(email)

    email_otps_collection.update_one(
        {
            "email": email,
            "purpose": purpose
        },
        {
            "$inc": {"attempts": 1}
        }
    )

    record = get_email_otp(email, purpose)

    return record.get("attempts", 0) if record else 0


def delete_email_otp(email, purpose):
    result = email_otps_collection.delete_one({
        "email": normalize_email(email),
        "purpose": purpose
    })

    return result.deleted_count > 0


# =========================================================
# PASSWORD FUNCTIONS
# =========================================================

def update_user_password(email, new_password):
    """
    Update password only for an existing verified account.
    """

    email = normalize_email(email)

    try:
        password_hash = hash_password(new_password)

        result = users_collection.update_one(
            {
                "email": email,
                "email_verified": True
            },
            {
                "$set": {
                    "password_hash": password_hash,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

        return result.matched_count == 1

    except Exception as error:
        print("[PASSWORD UPDATE ERROR]", type(error).__name__)
        return False


# =========================================================
# CONVERSATION FUNCTIONS
# =========================================================

def create_conversation(user_id, title="New Chat"):
    now = datetime.now(timezone.utc)

    document = {
        "user_id": ObjectId(user_id),
        "title": title,
        "created_at": now,
        "updated_at": now
    }

    result = conversations_collection.insert_one(document)

    return str(result.inserted_id)


def get_user_conversation(conversation_id, user_id):
    try:
        return conversations_collection.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": ObjectId(user_id)
        })

    except Exception:
        return None


def get_conversations(user_id):
    conversations = (
        conversations_collection
        .find({"user_id": ObjectId(user_id)})
        .sort("updated_at", DESCENDING)
    )

    result = []

    for conversation in conversations:
        result.append({
            "id": str(conversation["_id"]),
            "title": conversation.get("title", "New Chat"),
            "created_at": format_datetime(
                conversation.get("created_at")
            ),
            "updated_at": format_datetime(
                conversation.get("updated_at")
            )
        })

    return result


def delete_conversation(conversation_id, user_id):
    conversation = get_user_conversation(
        conversation_id,
        user_id
    )

    if not conversation:
        return False

    object_id = ObjectId(conversation_id)

    conversations_collection.delete_one({
        "_id": object_id,
        "user_id": ObjectId(user_id)
    })

    messages_collection.delete_many({
        "conversation_id": object_id
    })

    return True

def clear_conversation_messages(conversation_id, user_id):
    conversation = get_user_conversation(conversation_id, user_id)

    if not conversation:
        return False

    object_id = ObjectId(conversation_id)

    messages_collection.delete_many({
        "conversation_id": object_id
    })

    conversations_collection.update_one(
        {
            "_id": object_id,
            "user_id": ObjectId(user_id)
        },
        {
            "$set": {
                "title": "New Chat",
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return True
def update_conversation_title(conversation_id, user_id, title):
    conversation = get_user_conversation(
        conversation_id,
        user_id
    )

    if not conversation:
        return False

    result = conversations_collection.update_one(
        {
            "_id": ObjectId(conversation_id),
            "user_id": ObjectId(user_id)
        },
        {
            "$set": {
                "title": title,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return result.matched_count == 1


# =========================================================
# MESSAGE FUNCTIONS
# =========================================================

def add_message(conversation_id, role, message):
    now = datetime.now(timezone.utc)

    conversation_object_id = ObjectId(conversation_id)

    document = {
        "conversation_id": conversation_object_id,
        "role": role,
        "message": message,
        "created_at": now
    }

    result = messages_collection.insert_one(document)

    conversations_collection.update_one(
        {"_id": conversation_object_id},
        {
            "$set": {
                "updated_at": now
            }
        }
    )

    return str(result.inserted_id)


def get_messages(conversation_id):
    messages = (
        messages_collection
        .find({
            "conversation_id": ObjectId(conversation_id)
        })
        .sort("created_at", 1)
    )

    result = []

    for message in messages:
        result.append({
            "id": str(message["_id"]),
            "conversation_id": str(message["conversation_id"]),
            "role": message.get("role"),
            "message": message.get("message", ""),
            "image_url": message.get("image_url"),
            "created_at": format_datetime(
                message.get("created_at")
            )
        })

    return result


# =========================================================
# ANONYMOUS VISITOR CHAT FUNCTIONS
# =========================================================

def create_visitor_conversation(visitor_id, title="New Chat"):
    now = datetime.now(timezone.utc)

    document = {
        "visitor_id": visitor_id,
        "title": title,
        "created_at": now,
        "updated_at": now
    }

    result = conversations_collection.insert_one(document)

    return str(result.inserted_id)


def get_visitor_conversation(conversation_id, visitor_id):
    try:
        return conversations_collection.find_one({
            "_id": ObjectId(conversation_id),
            "visitor_id": visitor_id
        })

    except Exception:
        return None


def get_visitor_conversations(visitor_id):
    conversations = (
        conversations_collection
        .find({"visitor_id": visitor_id})
        .sort("updated_at", DESCENDING)
    )

    result = []

    for conversation in conversations:
        result.append({
            "id": str(conversation["_id"]),
            "title": conversation.get("title", "New Chat"),
            "created_at": format_datetime(
                conversation.get("created_at")
            ),
            "updated_at": format_datetime(
                conversation.get("updated_at")
            )
        })

    return result


def delete_visitor_conversation(conversation_id, visitor_id):
    conversation = get_visitor_conversation(
        conversation_id,
        visitor_id
    )

    if not conversation:
        return False

    object_id = ObjectId(conversation_id)

    conversations_collection.delete_one({
        "_id": object_id,
        "visitor_id": visitor_id
    })

    messages_collection.delete_many({
        "conversation_id": object_id
    })

    return True


def update_visitor_conversation_title(
    conversation_id,
    visitor_id,
    title
):
    conversation = get_visitor_conversation(
        conversation_id,
        visitor_id
    )

    if not conversation:
        return False

    result = conversations_collection.update_one(
        {
            "_id": ObjectId(conversation_id),
            "visitor_id": visitor_id
        },
        {
            "$set": {
                "title": title,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return result.matched_count == 1