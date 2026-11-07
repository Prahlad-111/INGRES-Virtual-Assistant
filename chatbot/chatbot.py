# =========================================================
# INGRES AI VIRTUAL ASSISTANT
# =========================================================

import os
import sys
import pickle
import random
import re


# =========================================================
# PROJECT ROOT
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# =========================================================
# IMPORTS
# =========================================================

from preprocessing.text_preprocessing import preprocess_text

from chatbot.responses import get_responses

from services.ai_service import ask_gemini


# =========================================================
# MODEL PATHS
# =========================================================

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "chatbot_model.pkl"
)


VECTORIZER_PATH = os.path.join(
    BASE_DIR,
    "models",
    "tfidf_vectorizer.pkl"
)


# =========================================================
# CHECK MODEL FILES
# =========================================================

if not os.path.exists(MODEL_PATH):

    raise FileNotFoundError(
        "\nchatbot_model.pkl not found!\n\n"
        "Please run:\n"
        "python training\\train.py\n"
    )


if not os.path.exists(VECTORIZER_PATH):

    raise FileNotFoundError(
        "\ntfidf_vectorizer.pkl not found!\n\n"
        "Please run:\n"
        "python training\\train.py\n"
    )


# =========================================================
# LOAD ML MODEL
# =========================================================

with open(
    MODEL_PATH,
    "rb"
) as file:

    model = pickle.load(file)


# =========================================================
# LOAD TF-IDF VECTORIZER
# =========================================================

with open(
    VECTORIZER_PATH,
    "rb"
) as file:

    vectorizer = pickle.load(file)


# =========================================================
# CALCULATION DETECTION
# =========================================================

def is_calculation(text):

    text = text.lower().strip()

    calculation_words = [
        "calculate",
        "calculator",
        "solve",
        "plus",
        "minus",
        "multiply",
        "divided by"
    ]

    if any(
        word in text
        for word in calculation_words
    ):

        return True


    # Simple mathematical expression

    if re.fullmatch(
        r"[\d\s\+\-\*\/\(\)\.\%]+",
        text
    ):

        return True


    return False


# =========================================================
# CALCULATOR
# =========================================================

def calculate_expression(text):

    try:

        expression = text.lower()


        # Remove calculator words

        expression = expression.replace(
            "calculate",
            ""
        )


        expression = expression.replace(
            "solve",
            ""
        )


        expression = expression.strip()


        # Convert common mathematical words

        expression = expression.replace(
            "plus",
            "+"
        )


        expression = expression.replace(
            "minus",
            "-"
        )


        expression = expression.replace(
            "multiply",
            "*"
        )


        expression = expression.replace(
            "divided by",
            "/"
        )


        # Safety check

        if not re.fullmatch(
            r"[\d\s\+\-\*\/\(\)\.\%]+",
            expression
        ):

            return None


        # Calculate

        result = eval(
            expression,
            {
                "__builtins__": {}
            },
            {}
        )


        return f"The answer is {result}."


    except Exception:

        return (
            "I couldn't calculate that. "
            "Please provide a valid mathematical expression."
        )


# =========================================================
# NORMALIZE USER MESSAGE
# =========================================================

def normalize_message(message):

    return (
        message
        .lower()
        .strip()
        .replace("?", "")
        .replace("!", "")
        .replace(".", "")
    )


# =========================================================
# GENERAL GREETINGS
# =========================================================

GREETING_MESSAGES = {

    "hi",
    "hello",
    "hey",
    "hii",
    "hiii",
    "helo",
    "helloo",
    "hlw",

    "good morning",
    "good afternoon",
    "good evening",
    "good night",
}


# =========================================================
# GENERAL ASSISTANT QUESTIONS
# =========================================================

WHAT_IS_INGRES_MESSAGES = {

    "what is ingres",
    "what is ingres ai",
    "what is ingres virtual assistant",
    "what is the ingres",
    "tell me about ingres",
    "tell me about ingres ai",
    "explain ingres",
    "define ingres",
    "what does ingres do",
    "what can ingres do"
}


# =========================================================
# GENERAL HELP QUESTIONS
# =========================================================

HELP_MESSAGES = {

    "help",
    "how can you help me",
    "what can you help me with",
    "what can you do",
    "how can you help",
    "tell me what you can do"
}


# =========================================================
# MAIN CHATBOT FUNCTION
# =========================================================

def get_response(
    user_message,
    conversation_history=None
):

    # =====================================================
    # VALIDATE INPUT
    # =====================================================

    if not user_message:

        return "Please enter a question."


    user_message = user_message.strip()


    if not user_message:

        return "Please enter a question."


    print(
        f"[USER] {user_message}"
    )


    # =====================================================
    # NORMALIZED MESSAGE
    # =====================================================

    normalized_message = normalize_message(
        user_message
    )


    # =====================================================
    # 0. GENERAL GREETING
    # =====================================================

    # Greetings are handled before ML.
    # This prevents "hello" or "hi" from being
    # incorrectly classified as another intent.

    if normalized_message in GREETING_MESSAGES:

        print(
            "[ROUTER] General Greeting"
        )


        return (
            "Hi! 👋 I am the INGRES virtual assistant. "
            "Tell me, how can I help you?"
        )


    # =====================================================
    # 0.1 WHAT IS THE ASSISTANT
    # =====================================================

    # This must be handled before ML so that "what is INGRES"
    # gets a normal virtual-assistant explanation.

    if normalized_message in WHAT_IS_INGRES_MESSAGES:

        print(
            "[ROUTER] INGRES Introduction"
        )


        return (
            "INGRES is a virtual assistant designed to help "
            "you find solutions to your problems. You can ask "
            "questions on a wide range of topics, and I’ll do "
            "my best to provide a clear and useful answer."
        )


    # =====================================================
    # 0.2 GENERAL HELP
    # =====================================================

    if normalized_message in HELP_MESSAGES:

        print(
            "[ROUTER] General Help"
        )


        return (
            "I can help you with questions, explanations, "
            "programming, mathematics, technology, "
            "cybersecurity, education, AI/ML, project "
            "development, and many other topics. "
            "Just tell me what you need."
        )


    # =====================================================
    # 1. CALCULATOR
    # =====================================================

    if is_calculation(
        user_message
    ):

        result = calculate_expression(
            user_message
        )


        if result:

            print(
                "[ROUTER] Calculator"
            )


            return result


    # =====================================================
    # 2. ML INTENT CLASSIFICATION
    # =====================================================

    try:

        processed_message = preprocess_text(
            user_message
        )


        if processed_message:

            message_vector = (
                vectorizer.transform(
                    [processed_message]
                )
            )


            predicted_intent = (
                model.predict(
                    message_vector
                )[0]
            )


            probabilities = (
                model.predict_proba(
                    message_vector
                )[0]
            )


            confidence = max(
                probabilities
            )


            print(
                f"[ROUTER] ML Intent: "
                f"{predicted_intent} | "
                f"Confidence: {confidence:.2f}"
            )


            # -------------------------------------------------
            # ML RESPONSE
            # -------------------------------------------------

            if confidence >= 0.30:

                response_list = get_responses(
                    predicted_intent
                )


                if response_list:

                    print(
                        "[ROUTER] ML Response"
                    )


                    return random.choice(
                        response_list
                    )


    except Exception as error:

        print(
            "[ML ERROR]",
            error
        )


    # =====================================================
    # 3. GROQ AI
    # =====================================================

    # Anything not handled by calculator or ML goes to Groq.

    print(
        "[ROUTER] Groq AI"
    )


    return ask_gemini(
        user_message,
        conversation_history
    )


# =========================================================
# COMMAND-LINE CHATBOT
# =========================================================

if __name__ == "__main__":

    print()

    print(
        "==================================="
    )

    print(
        "       INGRES AI VIRTUAL ASSISTANT"
    )

    print(
        "==================================="
    )

    print(
        "Ask me anything or type 'exit' to stop."
    )

    print(
        "-----------------------------------"
    )

    print()


    # =====================================================
    # CONVERSATION MEMORY
    # =====================================================

    conversation_history = []


    while True:

        try:

            user_input = input(
                "You: "
            )


            # =================================================
            # EXIT
            # =================================================

            if (
                user_input
                .lower()
                .strip()
                == "exit"
            ):

                print(
                    "Bot: Goodbye!"
                )

                break


            # =================================================
            # GET RESPONSE
            # =================================================

            response = get_response(
                user_input,
                conversation_history
            )


            print(
                "Bot:",
                response
            )


            print()


            # =================================================
            # SAVE USER MESSAGE
            # =================================================

            if user_input.strip():

                conversation_history.append({

                    "role":
                        "user",

                    "message":
                        user_input.strip()

                })


            # =================================================
            # SAVE ASSISTANT MESSAGE
            # =================================================

            conversation_history.append({

                "role":
                    "assistant",

                "message":
                    response

            })


            # =================================================
            # KEEP LAST 10 MESSAGES
            # =================================================

            conversation_history = (
                conversation_history[-10:]
            )


        except KeyboardInterrupt:

            print(
                "\nBot: Goodbye!"
            )

            break


        except Exception as error:

            print(
                "\nBot error:",
                error
            )

            print()