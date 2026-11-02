import os
from datetime import datetime, timezone

import bcrypt
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient, DESCENDING


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# MONGODB CONFIGURATION
# =========================================================

MONGO_URI = os.getenv("MONGO_URI")

DATABASE_NAME = "ingres_ai"


if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI is not set in the .env file."
    )


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
password_resets_collection = db["password_resets"]


# =========================================================
# CREATE UNIQUE EMAIL INDEX
# =========================================================

try:

    users_collection.create_index(
        "email",
        unique=True
    )

except Exception as error:

    print(
        "[INDEX WARNING]",
        error
    )

# =========================================================
# CREATE UNIQUE SECRET ID INDEX
# =========================================================

try:
    users_collection.create_index(
        "secret_id_hash",
        unique=True,
        sparse=True
    )
except Exception as error:
    print("[SECRET ID INDEX WARNING]", error)
# =========================================================
# TEST MONGODB CONNECTION
# =========================================================

def test_connection():

    try:

        client.admin.command("ping")

        print(
            "MongoDB connected successfully!"
        )

        print(
            f"Database: {DATABASE_NAME}"
        )

        print("Collections:")

        print(" - users")
        print(" - conversations")
        print(" - messages")

        return True

    except Exception as error:

        print(
            "MongoDB connection failed!"
        )

        print(
            "Error:",
            error
        )

        return False


# =========================================================
# CREATE USER
# =========================================================

def create_user(
    name,
    email,
    password
):

    name = name.strip()

    email = email.strip().lower()


    # Check whether email already exists

    existing_user = users_collection.find_one(
        {
            "email": email
        }
    )


    if existing_user:

        return None


    # Hash password

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


    now = datetime.now(
        timezone.utc
    )


    user_document = {

        "name": name,

        "email": email,

        "password_hash": password_hash,

        "created_at": now,

        "updated_at": now

    }


    try:

        result = users_collection.insert_one(
            user_document
        )

        return str(
            result.inserted_id
        )

    except Exception as error:

        print(
            "[CREATE USER ERROR]",
            error
        )

        return None


# =========================================================
# GET USER BY EMAIL
# =========================================================

def get_user_by_email(email):

    email = email.strip().lower()

    return users_collection.find_one(
        {
            "email": email
        }
    )


# =========================================================
# GET USER BY ID
# =========================================================

def get_user_by_id(user_id):

    try:

        return users_collection.find_one(
            {
                "_id": ObjectId(user_id)
            }
        )

    except Exception:

        return None


# =========================================================
# VERIFY PASSWORD
# =========================================================

def verify_password(
    password,
    password_hash
):

    try:

        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )

    except Exception:

        return False


# =========================================================
# CREATE CONVERSATION
# =========================================================

def create_conversation(
    user_id,
    title="New Chat"
):

    now = datetime.now(
        timezone.utc
    )


    document = {

        "user_id": ObjectId(user_id),

        "title": title,

        "created_at": now,

        "updated_at": now

    }


    result = conversations_collection.insert_one(
        document
    )


    return str(
        result.inserted_id
    )


# =========================================================
# GET USER CONVERSATION
# =========================================================

def get_user_conversation(
    conversation_id,
    user_id
):

    try:

        return conversations_collection.find_one(
            {
                "_id": ObjectId(conversation_id),

                "user_id": ObjectId(user_id)
            }
        )

    except Exception:

        return None


# =========================================================
# ADD MESSAGE
# =========================================================

def add_message(
    conversation_id,
    role,
    message
):

    now = datetime.now(
        timezone.utc
    )


    conversation_object_id = ObjectId(
        conversation_id
    )


    document = {

        "conversation_id":
            conversation_object_id,

        "role":
            role,

        "message":
            message,

        "created_at":
            now

    }


    result = messages_collection.insert_one(
        document
    )


    # Update conversation timestamp

    conversations_collection.update_one(

        {
            "_id":
                conversation_object_id
        },

        {
            "$set":
                {
                    "updated_at":
                        now
                }
        }

    )


    return str(
        result.inserted_id
    )


# =========================================================
# GET USER CONVERSATIONS
# =========================================================

def get_conversations(
    user_id
):

    user_object_id = ObjectId(
        user_id
    )


    conversations = (

        conversations_collection

        .find(
            {
                "user_id":
                    user_object_id
            }
        )

        .sort(
            "updated_at",
            DESCENDING
        )

    )


    result = []


    for conversation in conversations:

        result.append(

            {
                "id":
                    str(
                        conversation["_id"]
                    ),

                "title":
                    conversation.get(
                        "title",
                        "New Chat"
                    ),

                "created_at":
                    format_datetime(
                        conversation.get(
                            "created_at"
                        )
                    ),

                "updated_at":
                    format_datetime(
                        conversation.get(
                            "updated_at"
                        )
                    )
            }

        )


    return result


# =========================================================
# GET MESSAGES
# =========================================================

def get_messages(
    conversation_id
):

    messages = (

        messages_collection

        .find(
            {
                "conversation_id":
                    ObjectId(
                        conversation_id
                    )
            }
        )

        .sort(
            "created_at",
            1
        )

    )


    result = []


    for message in messages:

        result.append(

            {
                "id":
                    str(
                        message["_id"]
                    ),

                "conversation_id":
                    str(
                        message["conversation_id"]
                    ),

                "role":
                    message.get(
                        "role"
                    ),

                "message":
                    message.get(
                        "message",
                        ""
                    ),

                "created_at":
                    format_datetime(
                        message.get(
                            "created_at"
                        )
                    )
            }

        )


    return result


# =========================================================
# DELETE CONVERSATION
# =========================================================

def delete_conversation(
    conversation_id,
    user_id
):

    conversation = get_user_conversation(
        conversation_id,
        user_id
    )


    if not conversation:

        return False


    object_id = ObjectId(
        conversation_id
    )


    # Delete conversation

    conversations_collection.delete_one(
        {
            "_id": object_id,

            "user_id":
                ObjectId(user_id)
        }
    )


    # Delete all messages belonging
    # to the conversation

    messages_collection.delete_many(
        {
            "conversation_id":
                object_id
        }
    )


    return True


# =========================================================
# UPDATE CONVERSATION TITLE
# =========================================================

def update_conversation_title(
    conversation_id,
    user_id,
    title
):

    conversation = get_user_conversation(
        conversation_id,
        user_id
    )


    if not conversation:

        return False


    conversations_collection.update_one(

        {
            "_id":
                ObjectId(conversation_id),

            "user_id":
                ObjectId(user_id)
        },

        {
            "$set":
                {
                    "title":
                        title,

                    "updated_at":
                        datetime.now(
                            timezone.utc
                        )
                }
        }

    )


    return True


# =========================================================
# FORMAT DATETIME
# =========================================================

def format_datetime(
    value
):

    if value is None:

        return None


    if isinstance(
        value,
        datetime
    ):

        return value.strftime(
            "%Y-%m-%d %H:%M:%S"
        )


    return str(value)

# =========================================================
# EMAIL OTP - PENDING REGISTRATION FUNCTIONS
# =========================================================

# MongoDB automatically removes expired pending registrations.
try:
    pending_registrations_collection.create_index(
        "expires_at",
        expireAfterSeconds=0
    )
except Exception as error:
    print("[PENDING REGISTRATION INDEX WARNING]", error)


def save_pending_registration(
    name,
    email,
    password,
    otp_hash,
    expires_at
):
    """Save a pending registration without activating the account."""

    name = name.strip()
    email = email.strip().lower()

    try:
        # Never store the password in plain text.
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

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
        print("[SAVE PENDING REGISTRATION ERROR]", error)
        return False


def get_pending_registration(email):
    """Find a pending registration by email."""

    return pending_registrations_collection.find_one({
        "email": email.strip().lower()
    })


def increment_pending_otp_attempts(email):
    """Increase the number of OTP verification attempts."""

    email = email.strip().lower()

    pending_registrations_collection.update_one(
        {"email": email},
        {"$inc": {"attempts": 1}}
    )

    pending = get_pending_registration(email)

    return pending.get("attempts", 0) if pending else 0


def delete_pending_registration(email):
    """Delete a pending registration."""

    result = pending_registrations_collection.delete_one({
        "email": email.strip().lower()
    })

    return result.deleted_count > 0


def create_verified_user_from_pending(email):
    """Create the permanent account after OTP verification."""

    email = email.strip().lower()
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

        # Remove the pending record only after account creation succeeds.
        delete_pending_registration(email)

        return str(result.inserted_id)

    except Exception as error:
        print("[CREATE VERIFIED USER ERROR]", error)
        return None

# =====================================================
# FORGOT PASSWORD - UPDATE PASSWORD
# =====================================================

def update_user_password(email, new_password):
    """
    Update a user's password securely using bcrypt.
    The caller must verify the password-reset OTP first.
    """

    email = email.strip().lower()

    if not new_password or len(new_password) < 6:
        return False

    if len(new_password) > 72:
        return False

    try:
        # Hash the new password before saving it.
        password_hash = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

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

        return result.modified_count == 1

    except Exception as error:
        print("[PASSWORD UPDATE ERROR]", error)
        return False

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
        conversation_id, visitor_id
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
    conversation_id, visitor_id, title
):
    conversation = get_visitor_conversation(
        conversation_id, visitor_id
    )

    if not conversation:
        return False

    conversations_collection.update_one(
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

    return True

# =========================================================
# INGRES SECRET ID ACCOUNT SYSTEM
# =========================================================

import secrets
import hashlib


def generate_secret_id():
    """Generate a unique INGRES Secret ID."""

    while True:
        secret_id = "ING-" + secrets.token_hex(6).upper()

        secret_hash = hashlib.sha256(
            secret_id.encode("utf-8")
        ).hexdigest()

        existing = users_collection.find_one({
            "secret_id_hash": secret_hash
        })

        if not existing:
            return secret_id


def create_secret_id_user(name):
    """Create a new account using the user's name."""

    name = name.strip()

    if not name or len(name) > 100:
        return None

    secret_id = generate_secret_id()

    secret_hash = hashlib.sha256(
        secret_id.encode("utf-8")
    ).hexdigest()

    now = datetime.now(timezone.utc)

    user_document = {
        "name": name,
        "secret_id_hash": secret_hash,
        "login_method": "secret_id",
        "created_at": now,
        "updated_at": now
    }

    try:
        result = users_collection.insert_one(user_document)

        return {
            "user_id": str(result.inserted_id),
            "name": name,
            "secret_id": secret_id
        }

    except Exception as error:
        print("[SECRET ID ACCOUNT ERROR]", error)
        return None


def login_with_secret_id(name, secret_id):
    """Find an account using name and Secret ID."""

    name = name.strip()
    secret_id = secret_id.strip().upper()

    if not name or not secret_id:
        return None

    secret_hash = hashlib.sha256(
        secret_id.encode("utf-8")
    ).hexdigest()

    user = users_collection.find_one({
        "name": name,
        "secret_id_hash": secret_hash,
        "login_method": "secret_id"
    })

    if not user:
        return None

    return {
        "user_id": str(user["_id"]),
        "name": user["name"]
    }
