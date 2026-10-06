from flask import Blueprint, request, jsonify

from chatbot.chatbot import get_response

from database.mongodb import (
    create_conversation,
    add_message,
    get_conversations,
    get_messages,
    get_user_conversation,
    delete_conversation,
    update_conversation_title
)

from api.auth import token_required


# =========================================================
# CREATE BLUEPRINT
# =========================================================

chatbot_api = Blueprint(
    "chatbot_api",
    __name__
)


# =========================================================
# CHAT API
# =========================================================

@chatbot_api.route("/chat", methods=["POST"])
@token_required
def chat():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data received."
            }), 400

        # -------------------------------------------------
        # USER MESSAGE
        # -------------------------------------------------

        user_message = data.get("message", "")

        if not isinstance(user_message, str):
            return jsonify({
                "success": False,
                "message": "Invalid message."
            }), 400

        user_message = user_message.strip()

        if not user_message:
            return jsonify({
                "success": False,
                "message": "Please enter a message."
            }), 400

        # -------------------------------------------------
        # LOGGED-IN USER
        # -------------------------------------------------

        user_id = request.user_id

        # -------------------------------------------------
        # CONVERSATION ID
        # -------------------------------------------------

        conversation_id = data.get("conversation_id")

        # -------------------------------------------------
        # CREATE NEW CONVERSATION
        # -------------------------------------------------

        if not conversation_id:

            title = user_message

            if len(title) > 40:
                title = title[:40] + "..."

            conversation_id = create_conversation(
                user_id,
                title
            )

        else:

            # Verify that this conversation belongs
            # to the logged-in user.

            conversation = get_user_conversation(
                conversation_id,
                user_id
            )

            if not conversation:

                return jsonify({
                    "success": False,
                    "message": "Conversation not found."
                }), 404

        # -------------------------------------------------
        # GET PREVIOUS CONVERSATION HISTORY
        # -------------------------------------------------

        old_messages = get_messages(
            conversation_id
        )

        conversation_history = []

        for item in old_messages:

            role = item.get("role")

            message = item.get(
                "message",
                ""
            )

            if role in ["user", "assistant"]:

                conversation_history.append({
                    "role": role,
                    "message": message
                })

        # -------------------------------------------------
        # SAVE USER MESSAGE
        # -------------------------------------------------

        add_message(
            conversation_id,
            "user",
            user_message
        )

        # -------------------------------------------------
        # GET AI RESPONSE
        # -------------------------------------------------

        try:

            bot_response = get_response(
                user_message,
                conversation_history
            )

        except TypeError:

            # Compatibility with older chatbot code.

            bot_response = get_response(
                user_message
            )

        # -------------------------------------------------
        # SAVE AI RESPONSE
        # -------------------------------------------------

        add_message(
            conversation_id,
            "assistant",
            bot_response
        )

        # -------------------------------------------------
        # RETURN RESPONSE
        # -------------------------------------------------

        return jsonify({
            "success": True,
            "conversation_id": conversation_id,
            "user_message": user_message,
            "response": bot_response
        })

    except Exception as error:

        print(
            "[CHAT API ERROR]",
            error
        )

        return jsonify({
            "success": False,
            "message": "Something went wrong."
        }), 500


# =========================================================
# GET RECENT CHATS
# =========================================================

@chatbot_api.route("/chats", methods=["GET"])
@token_required
def get_all_chats():

    try:

        user_id = request.user_id

        chats = get_conversations(
            user_id
        )

        return jsonify({
            "success": True,
            "chats": chats
        })

    except Exception as error:

        print(
            "[GET CHATS ERROR]",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to load chat history."
        }), 500


# =========================================================
# CREATE NEW CHAT
# =========================================================

@chatbot_api.route("/chats", methods=["POST"])
@token_required
def create_new_chat():

    try:

        data = request.get_json() or {}

        title = data.get(
            "title",
            "New Chat"
        )

        if not isinstance(title, str):
            title = "New Chat"

        title = title.strip()

        if not title:
            title = "New Chat"

        conversation_id = create_conversation(
            request.user_id,
            title
        )

        return jsonify({
            "success": True,
            "conversation_id": conversation_id,
            "title": title
        }), 201

    except Exception as error:

        print(
            "[CREATE CHAT ERROR]",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to create chat."
        }), 500


# =========================================================
# OPEN CONVERSATION
# =========================================================

@chatbot_api.route(
    "/chats/<conversation_id>",
    methods=["GET"]
)
@token_required
def get_chat_messages(conversation_id):

    try:

        conversation = get_user_conversation(
            conversation_id,
            request.user_id
        )

        if not conversation:

            return jsonify({
                "success": False,
                "message": "Conversation not found."
            }), 404

        messages = get_messages(
            conversation_id
        )

        return jsonify({
            "success": True,
            "conversation_id": conversation_id,
            "title": conversation.get(
                "title",
                "New Chat"
            ),
            "messages": messages
        })

    except Exception as error:

        print(
            "[GET MESSAGES ERROR]",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to load messages."
        }), 500


# =========================================================
# DELETE CONVERSATION
# =========================================================

@chatbot_api.route(
    "/chats/<conversation_id>",
    methods=["DELETE"]
)
@token_required
def remove_chat(conversation_id):

    try:

        deleted = delete_conversation(
            conversation_id,
            request.user_id
        )

        if not deleted:

            return jsonify({
                "success": False,
                "message": "Chat not found."
            }), 404

        return jsonify({
            "success": True,
            "message": "Chat deleted successfully."
        })

    except Exception as error:

        print(
            "[DELETE CHAT ERROR]",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to delete chat."
        }), 500


# =========================================================
# RENAME CONVERSATION
# =========================================================

@chatbot_api.route(
    "/chats/<conversation_id>",
    methods=["PUT"]
)
@token_required
def rename_chat(conversation_id):

    try:

        data = request.get_json() or {}

        title = data.get(
            "title",
            ""
        )

        if not isinstance(title, str):
            title = ""

        title = title.strip()

        if not title:

            return jsonify({
                "success": False,
                "message": "Chat title cannot be empty."
            }), 400

        updated = update_conversation_title(
            conversation_id,
            request.user_id,
            title
        )

        if not updated:

            return jsonify({
                "success": False,
                "message": "Chat not found."
            }), 404

        return jsonify({
            "success": True,
            "message": "Chat renamed successfully.",
            "conversation_id": conversation_id,
            "title": title
        })

    except Exception as error:

        print(
            "[RENAME CHAT ERROR]",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to rename chat."
        }), 500