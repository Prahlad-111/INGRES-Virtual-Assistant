import os
import sys
import pickle
import random
import re


# ==================================================
# PROJECT ROOT
# ==================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ==================================================
# IMPORTS
# ==================================================

from preprocessing.text_preprocessing import preprocess_text

from chatbot.responses import get_responses

from services.location_service import get_location_response

from services.ingres_service import get_groundwater_information

from services.ai_service import ask_gemini


# ==================================================
# MODEL PATHS
# ==================================================

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


# ==================================================
# CHECK MODEL FILES
# ==================================================

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


# ==================================================
# LOAD ML MODEL
# ==================================================

with open(
    MODEL_PATH,
    "rb"
) as file:

    model = pickle.load(file)


# ==================================================
# LOAD TF-IDF VECTORIZER
# ==================================================

with open(
    VECTORIZER_PATH,
    "rb"
) as file:

    vectorizer = pickle.load(file)


# ==================================================
# CALCULATION DETECTION
# ==================================================

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


    # Detect simple mathematical expressions

    if re.fullmatch(
        r"[\d\s\+\-\*\/\(\)\.\%]+",
        text
    ):

        return True


    return False


# ==================================================
# CALCULATOR
# ==================================================

def calculate_expression(text):

    try:

        expression = text.lower()


        expression = expression.replace(
            "calculate",
            ""
        )


        expression = expression.replace(
            "solve",
            ""
        )


        expression = expression.strip()


        # --------------------------------------------------
        # Convert common mathematical words
        # --------------------------------------------------

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


        # --------------------------------------------------
        # Safety check
        # --------------------------------------------------

        if not re.fullmatch(
            r"[\d\s\+\-\*\/\(\)\.\%]+",
            expression
        ):

            return None


        # --------------------------------------------------
        # Calculate
        # --------------------------------------------------

        result = eval(
            expression,
            {
                "__builtins__": {}
            },
            {}
        )


        return (
            f"The answer is {result}."
        )


    except Exception:

        return (
            "I couldn't calculate that. "
            "Please provide a valid mathematical expression."
        )


# ==================================================
# MAIN CHATBOT FUNCTION
# ==================================================

def get_response(
    user_message,
    conversation_history=None
):

    # --------------------------------------------------
    # Validate input
    # --------------------------------------------------

    if not user_message:

        return "Please enter a question."


    user_message = user_message.strip()


    if not user_message:

        return "Please enter a question."


    print(
        f"[USER] {user_message}"
    )


    # ==================================================
    # 1. CALCULATOR
    # ==================================================

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


    # ==================================================
    # 2. INGRES / GROUNDWATER DATA
    # ==================================================

    try:

        location_result = get_location_response(
            user_message
        )


        if location_result:

            if location_result.get(
                "location_found"
            ):

                state = location_result.get(
                    "state"
                )


                groundwater_keywords = [

                    "groundwater",
                    "ground water",
                    "recharge",
                    "extraction",
                    "extractable",
                    "resource",
                    "assessment",
                    "status",
                    "category",
                    "safe",
                    "critical",
                    "over exploited",
                    "over-exploited",
                    "data"

                ]


                lower_message = (
                    user_message.lower()
                )


                if any(
                    keyword in lower_message
                    for keyword in groundwater_keywords
                ):

                    print(
                        f"[ROUTER] INGRES Data → {state}"
                    )


                    return get_groundwater_information(
                        state
                    )


    except Exception as error:

        print(
            "[INGRES ERROR]",
            error
        )


    # ==================================================
    # 3. ML INTENT CLASSIFICATION
    # ==================================================

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


            # --------------------------------------------------
            # Use ML response only when confidence is reasonable
            # --------------------------------------------------

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


    # ==================================================
    # 4. GEMINI AI
    # ==================================================

    print(
        ("[ROUTER] Groq AI")
    )


    return ask_gemini(

        user_message,

        conversation_history

    )


# ==================================================
# COMMAND-LINE CHATBOT
# ==================================================

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


    # --------------------------------------------------
    # Command-line conversation memory
    # --------------------------------------------------

    conversation_history = []


    while True:

        try:

            user_input = input(
                "You: "
            )


            # --------------------------------------------------
            # Exit
            # --------------------------------------------------

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


            # --------------------------------------------------
            # Get response
            # --------------------------------------------------

            response = get_response(

                user_input,

                conversation_history

            )


            print(
                "Bot:",
                response
            )


            print()


            # --------------------------------------------------
            # Save user message
            # --------------------------------------------------

            if user_input.strip():

                conversation_history.append({

                    "role": "user",

                    "message": user_input.strip()

                })


            # --------------------------------------------------
            # Save bot response
            # --------------------------------------------------

            conversation_history.append({

                "role": "assistant",

                "message": response

            })


            # --------------------------------------------------
            # Keep latest 10 messages
            # --------------------------------------------------

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