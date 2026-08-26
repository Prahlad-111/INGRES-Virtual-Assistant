from flask import Blueprint, request, jsonify

from chatbot.chatbot import get_response


# ==================================================
# CREATE API BLUEPRINT
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

        print("\n================ API REQUEST ================")
        print("Received data:", data)


        if not data:

            return jsonify({
                "success": False,
                "message": "No data received."
            }), 400


        user_message = data.get(
            "message",
            ""
        )


        if not isinstance(
            user_message,
            str
        ):

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


        # ==================================================
        # CONVERSATION HISTORY
        # ==================================================

        conversation_history = data.get(
            "conversation_history",
            []
        )


        if not isinstance(
            conversation_history,
            list
        ):

            conversation_history = []


        conversation_history = (
            conversation_history[-10:]
        )


        print(
            "User message:",
            user_message
        )

        print(
            "History:",
            conversation_history
        )


        # ==================================================
        # GET CHATBOT RESPONSE
        # ==================================================

        bot_response = get_response(

            user_message,

            conversation_history

        )


        print(
            "Bot response generated successfully."
        )

        print("============================================\n")


        return jsonify({

            "success": True,

            "user_message": user_message,

            "response": bot_response

        })


    except Exception as error:

        # ==================================================
        # SHOW ACTUAL ERROR
        # ==================================================

        print("\n!!!!!!!!!!!!!!! API ERROR !!!!!!!!!!!!!!!")

        print(
            "Error type:",
            type(error).__name__
        )

        print(
            "Error:",
            str(error)
        )

        import traceback

        traceback.print_exc()

        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")


        return jsonify({

            "success": False,

            "message": str(error),

            "error_type": type(error).__name__

        }), 500