from flask import Blueprint, request, jsonify

from chatbot.chatbot import get_response

from database.database import (
    create_conversation,
    add_message,
    get_conversations,
    get_messages,
    delete_conversation,
    update_conversation_title
)


# ==================================================
# CREATE BLUEPRINT
# ==================================================

chatbot_api = Blueprint(
    "chatbot_api",
    __name__
)


# ==================================================
# CHAT API
# ==================================================

@chatbot_api.route(
    "/chat",
    methods=["POST"]
)
def chat():

    try:

        data = request.get_json()


        # --------------------------------------------------
        # CHECK DATA
        # --------------------------------------------------

        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No data received."

            }), 400


        # --------------------------------------------------
        # GET USER MESSAGE
        # --------------------------------------------------

        user_message = data.get(
            "message",
            ""
        )


        if not user_message.strip():

            return jsonify({

                "success": False,

                "message":
                    "Please enter a message."

            }), 400


        # --------------------------------------------------
        # GET CONVERSATION ID
        # --------------------------------------------------

        conversation_id = data.get(
            "conversation_id"
        )


        # --------------------------------------------------
        # GET CONVERSATION HISTORY
        # --------------------------------------------------

        conversation_history = data.get(
            "conversation_history",
            []
        )


        # --------------------------------------------------
        # CREATE CONVERSATION IF NEEDED
        # --------------------------------------------------

        if not conversation_id:

            # Use first part of the message
            # as the initial chat title.

            title = user_message.strip()


            if len(title) > 40:

                title = (
                    title[:40]
                    + "..."
                )


            conversation_id = create_conversation(
                title
            )


        # --------------------------------------------------
        # SAVE USER MESSAGE
        # --------------------------------------------------

        add_message(

            conversation_id,

            "user",

            user_message

        )


        # --------------------------------------------------
        # GET AI RESPONSE
        # --------------------------------------------------

        try:

            bot_response = get_response(

                user_message,

                conversation_history

            )

        except TypeError:

            # Compatibility with an older
            # get_response() that accepts
            # only one argument.

            bot_response = get_response(
                user_message
            )


        # --------------------------------------------------
        # SAVE AI RESPONSE
        # --------------------------------------------------

        add_message(

            conversation_id,

            "assistant",

            bot_response

        )


        # --------------------------------------------------
        # RESPONSE
        # --------------------------------------------------

        return jsonify({

            "success": True,

            "conversation_id":
                conversation_id,

            "user_message":
                user_message,

            "response":
                bot_response

        })


    except Exception as error:

        print(
            "API Error:",
            error
        )


        return jsonify({

            "success": False,

            "message":
                "Something went wrong."

        }), 500


# ==================================================
# GET ALL CONVERSATIONS
# ==================================================

@chatbot_api.route(
    "/chats",
    methods=["GET"]
)
def get_all_chats():

    try:

        chats = get_conversations()


        return jsonify({

            "success": True,

            "chats":
                chats

        })


    except Exception as error:

        print(
            "Get chats error:",
            error
        )


        return jsonify({

            "success": False,

            "message":
                "Unable to load chat history."

        }), 500


# ==================================================
# CREATE NEW CONVERSATION
# ==================================================

@chatbot_api.route(
    "/chats",
    methods=["POST"]
)
def create_new_chat():

    try:

        data = request.get_json() or {}


        title = data.get(
            "title",
            "New Chat"
        )


        if not title.strip():

            title = "New Chat"


        conversation_id = create_conversation(
            title
        )


        return jsonify({

            "success": True,

            "conversation_id":
                conversation_id,

            "title":
                title

        }), 201


    except Exception as error:

        print(
            "Create chat error:",
            error
        )


        return jsonify({

            "success": False,

            "message":
                "Unable to create chat."

        }), 500


# ==================================================
# GET MESSAGES FOR A CONVERSATION
# ==================================================

@chatbot_api.route(
    "/chats/<int:conversation_id>",
    methods=["GET"]
)
def get_chat_messages(
    conversation_id
):

    try:

        messages = get_messages(
            conversation_id
        )


        return jsonify({

            "success": True,

            "conversation_id":
                conversation_id,

            "messages":
                messages

        })


    except Exception as error:

        print(
            "Get messages error:",
            error
        )


        return jsonify({

            "success": False,

            "message":
                "Unable to load messages."

        }), 500


# ==================================================
# DELETE CONVERSATION
# ==================================================

@chatbot_api.route(
    "/chats/<int:conversation_id>",
    methods=["DELETE"]
)
def remove_chat(
    conversation_id
):

    try:

        delete_conversation(
            conversation_id
        )


        return jsonify({

            "success": True,

            "message":
                "Chat deleted successfully."

        })


    except Exception as error:

        print(
            "Delete chat error:",
            error
        )


        return jsonify({

            "success": False,

            "message":
                "Unable to delete chat."

        }), 500


# ==================================================
# UPDATE CHAT TITLE
# ==================================================

@chatbot_api.route(
    "/chats/<int:conversation_id>",
    methods=["PUT"]
)
def rename_chat(
    conversation_id
):

    try:

        data = request.get_json() or {}


        title = data.get(
            "title",
            ""
        ).strip()


        if not title:

            return jsonify({

                "success": False,

                "message":
                    "Chat title cannot be empty."

            }), 400


        update_conversation_title(

            conversation_id,

            title

        )


        return jsonify({

            "success": True,

            "message":
                "Chat renamed successfully.",

            "conversation_id":
                conversation_id,

            "title":
                title

        })


    except Exception as error:

        print(
            "Rename chat error:",
            error
        )


        return jsonify({

            "success": False,

            "message":
                "Unable to rename chat."

        }), 500