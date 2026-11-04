from flask import Blueprint, jsonify, request

from api.auth import token_required
from chatbot.chatbot import get_response
from database.mongodb import (
    add_message,
    clear_conversation_messages,
    create_conversation,
    delete_conversation,
    get_conversations,
    get_messages,
    get_user_conversation,
    update_conversation_title,
)


chatbot_api = Blueprint("chatbot_api", __name__)


@chatbot_api.route("/chat", methods=["POST"])
@token_required
def chat():
    try:
        data = request.get_json(silent=True) or {}
        user_message = data.get("message", "")

        if not isinstance(user_message, str):
            return jsonify({
                "success": False,
                "message": "Invalid message.",
            }), 400

        user_message = user_message.strip()
        if not user_message:
            return jsonify({
                "success": False,
                "message": "Please enter a message.",
            }), 400

        conversation_id = data.get("conversation_id")

        if not conversation_id:
            title = user_message[:40]
            if len(user_message) > 40:
                title += "..."

            conversation_id = create_conversation(
                request.user_id,
                title,
            )
        elif not get_user_conversation(conversation_id, request.user_id):
            return jsonify({
                "success": False,
                "message": "Conversation not found.",
            }), 404

        history = [
            {
                "role": item.get("role"),
                "message": item.get("message", ""),
            }
            for item in get_messages(conversation_id)
            if item.get("role") in ("user", "assistant")
        ]

        add_message(conversation_id, "user", user_message)

        try:
            bot_response = get_response(user_message, history)
        except TypeError:
            bot_response = get_response(user_message)

        add_message(conversation_id, "assistant", bot_response)

        return jsonify({
            "success": True,
            "conversation_id": conversation_id,
            "user_message": user_message,
            "response": bot_response,
        }), 200

    except Exception as error:
        print("[CHAT API ERROR]", error)
        return jsonify({
            "success": False,
            "message": "Something went wrong.",
        }), 500


@chatbot_api.route("/chats", methods=["GET"])
@token_required
def get_all_chats():
    try:
        return jsonify({
            "success": True,
            "chats": get_conversations(request.user_id),
        }), 200
    except Exception as error:
        print("[GET CHATS ERROR]", error)
        return jsonify({
            "success": False,
            "message": "Unable to load chat history.",
        }), 500


@chatbot_api.route("/chats", methods=["POST"])
@token_required
def create_new_chat():
    try:
        data = request.get_json(silent=True) or {}
        title = data.get("title", "New Chat")

        if not isinstance(title, str):
            title = "New Chat"

        title = title.strip() or "New Chat"
        conversation_id = create_conversation(request.user_id, title)

        return jsonify({
            "success": True,
            "conversation_id": conversation_id,
            "title": title,
        }), 201
    except Exception as error:
        print("[CREATE CHAT ERROR]", error)
        return jsonify({
            "success": False,
            "message": "Unable to create chat.",
        }), 500


@chatbot_api.route("/chats/<conversation_id>", methods=["GET"])
@token_required
def get_chat_messages(conversation_id):
    try:
        conversation = get_user_conversation(
            conversation_id,
            request.user_id,
        )

        if not conversation:
            return jsonify({
                "success": False,
                "message": "Conversation not found.",
            }), 404

        return jsonify({
            "success": True,
            "conversation_id": conversation_id,
            "title": conversation.get("title", "New Chat"),
            "messages": get_messages(conversation_id),
        }), 200
    except Exception as error:
        print("[GET MESSAGES ERROR]", error)
        return jsonify({
            "success": False,
            "message": "Unable to load messages.",
        }), 500


@chatbot_api.route("/chats/<conversation_id>", methods=["DELETE"])
@token_required
def remove_chat(conversation_id):
    try:
        deleted = delete_conversation(
            conversation_id,
            request.user_id,
        )

        if not deleted:
            return jsonify({
                "success": False,
                "message": "Chat not found.",
            }), 404

        return jsonify({
            "success": True,
            "message": "Chat deleted successfully.",
        }), 200
    except Exception as error:
        print("[DELETE CHAT ERROR]", error)
        return jsonify({
            "success": False,
            "message": "Unable to delete chat.",
        }), 500


@chatbot_api.route(
    "/chats/<conversation_id>/messages",
    methods=["DELETE"],
)
@token_required
def clear_chat_memory(conversation_id):
    try:
        cleared = clear_conversation_messages(
            conversation_id,
            request.user_id,
        )

        if not cleared:
            return jsonify({
                "success": False,
                "message": "Chat not found.",
            }), 404

        return jsonify({
            "success": True,
            "message": "Conversation memory cleared.",
        }), 200
    except Exception as error:
        print("[CLEAR CHAT MEMORY ERROR]", error)
        return jsonify({
            "success": False,
            "message": "Unable to clear conversation memory.",
        }), 500


@chatbot_api.route("/chats/<conversation_id>", methods=["PUT"])
@token_required
def rename_chat(conversation_id):
    try:
        data = request.get_json(silent=True) or {}
        title = data.get("title", "")

        if not isinstance(title, str):
            title = ""

        title = title.strip()
        if not title:
            return jsonify({
                "success": False,
                "message": "Chat title cannot be empty.",
            }), 400

        updated = update_conversation_title(
            conversation_id,
            request.user_id,
            title,
        )

        if not updated:
            return jsonify({
                "success": False,
                "message": "Chat not found.",
            }), 404

        return jsonify({
            "success": True,
            "message": "Chat renamed successfully.",
            "conversation_id": conversation_id,
            "title": title,
        }), 200
    except Exception as error:
        print("[RENAME CHAT ERROR]", error)
        return jsonify({
            "success": False,
            "message": "Unable to rename chat.",
        }), 500