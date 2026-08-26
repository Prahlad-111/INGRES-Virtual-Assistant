import os

from dotenv import load_dotenv
from groq import Groq


# ==================================================
# LOAD ENVIRONMENT VARIABLES
# ==================================================

load_dotenv()


# ==================================================
# GROQ API KEY
# ==================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


if not GROQ_API_KEY:

    print(
        "[WARNING] GROQ_API_KEY is not configured."
    )

    client = None

else:

    client = Groq(
        api_key=GROQ_API_KEY
    )


# ==================================================
# GROQ MODEL
# ==================================================

MODEL_NAME = "openai/gpt-oss-120b"


# ==================================================
# SYSTEM PROMPT
# ==================================================

SYSTEM_PROMPT = """
You are INGRES AI, an intelligent and helpful virtual assistant.

You are NOT limited to groundwater questions.

You can help users with:

- General knowledge
- Artificial Intelligence
- Machine Learning
- Deep Learning
- NLP
- Programming
- Python
- Java
- C/C++
- JavaScript
- HTML and CSS
- Web development
- Cybersecurity
- Computer networks
- Databases and SQL
- Mathematics
- Science
- Education
- College and academic questions
- Project development
- Debugging
- Writing and explanations
- Technology
- INGRES and groundwater information
- Everyday questions

Give clear, accurate and useful answers.

Use simple language when the user asks for a simple explanation.

If the user asks for programming code, provide complete and working code
and briefly explain how it works.

If the user asks a technical question, explain the solution step by step.

Do not unnecessarily restrict your answers to groundwater or INGRES.

You are the general-purpose AI assistant inside the INGRES AI project.
"""


# ==================================================
# ASK GROQ
# ==================================================

def ask_groq(
    user_message,
    conversation_history=None
):

    """
    Send a user message to Groq AI.

    Parameters:
        user_message:
            Current question from the user.

        conversation_history:
            Optional previous conversation messages.

    Returns:
        AI-generated response as a string.
    """


    # --------------------------------------------------
    # CHECK API CLIENT
    # --------------------------------------------------

    if client is None:

        return (
            "Groq AI is not configured.\n\n"
            "Please check the GROQ_API_KEY "
            "in your .env file."
        )


    try:

        # --------------------------------------------------
        # CREATE MESSAGE LIST
        # --------------------------------------------------

        messages = [

            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }

        ]


        # --------------------------------------------------
        # ADD PREVIOUS CONVERSATION
        # --------------------------------------------------

        if conversation_history:

            for item in conversation_history:

                if not isinstance(
                    item,
                    dict
                ):
                    continue


                role = item.get(
                    "role"
                )


                message = item.get(
                    "message"
                )


                if not message:

                    continue


                # User message

                if role == "user":

                    messages.append({

                        "role": "user",

                        "content": str(
                            message
                        )

                    })


                # Assistant message

                elif role in (
                    "assistant",
                    "bot"
                ):

                    messages.append({

                        "role": "assistant",

                        "content": str(
                            message
                        )

                    })


        # --------------------------------------------------
        # ADD CURRENT USER MESSAGE
        # --------------------------------------------------

        messages.append({

            "role": "user",

            "content": str(
                user_message
            )

        })


        # --------------------------------------------------
        # SEND REQUEST TO GROQ
        # --------------------------------------------------

        response = client.chat.completions.create(

            model=MODEL_NAME,

            messages=messages,

            temperature=0.7,

            max_tokens=2048

        )


        # --------------------------------------------------
        # GET RESPONSE
        # --------------------------------------------------

        if not response.choices:

            return (
                "I couldn't generate a response. "
                "Please try again."
            )


        answer = (
            response
            .choices[0]
            .message
            .content
        )


        if not answer:

            return (
                "I couldn't generate a response. "
                "Please try again."
            )


        return answer.strip()


    # ==================================================
    # ERROR HANDLING
    # ==================================================

    except Exception as error:

        error_text = str(
            error
        )


        print(
            "[GROQ ERROR]",
            error_text
        )


        # --------------------------------------------------
        # RATE LIMIT / QUOTA
        # --------------------------------------------------

        if (

            "429" in error_text

            or

            "rate_limit" in
            error_text.lower()

            or

            "rate limit" in
            error_text.lower()

            or

            "quota" in
            error_text.lower()

        ):

            return (
                "Groq AI is temporarily unavailable "
                "because the API rate limit has been "
                "reached.\n\n"
                "Please wait a little while and try again."
            )


        # --------------------------------------------------
        # INVALID API KEY
        # --------------------------------------------------

        if (

            "401" in error_text

            or

            "authentication" in
            error_text.lower()

            or

            "invalid api key" in
            error_text.lower()

            or

            "unauthorized" in
            error_text.lower()

        ):

            return (
                "The Groq API key is invalid or "
                "not configured correctly.\n\n"
                "Please check your .env file."
            )


        # --------------------------------------------------
        # MODEL NOT FOUND
        # --------------------------------------------------

        if (

            "404" in error_text

            or

            "model_not_found" in
            error_text.lower()

            or

            "does not exist" in
            error_text.lower()

        ):

            return (
                "The selected Groq AI model is not "
                "available for this API key.\n\n"
                "Please check the available Groq models."
            )


        # --------------------------------------------------
        # CONNECTION ERROR
        # --------------------------------------------------

        if (

            "connection" in
            error_text.lower()

            or

            "timeout" in
            error_text.lower()

        ):

            return (
                "I couldn't connect to Groq AI.\n\n"
                "Please check your internet connection "
                "and try again."
            )


        # --------------------------------------------------
        # GENERAL ERROR
        # --------------------------------------------------

        return (
            "I'm currently unable to connect to "
            "Groq AI.\n\n"
            "Please try again later."
        )


# ==================================================
# COMPATIBILITY FUNCTION
# ==================================================

def ask_gemini(
    user_message,
    conversation_history=None
):

    """
    Compatibility function.

    Your existing chatbot may still call:

        ask_gemini()

    We keep this function so you don't have to
    immediately modify every existing file.

    Internally it now uses Groq.
    """

    return ask_groq(

        user_message,

        conversation_history

    )


# ==================================================
# TEST FUNCTION
# ==================================================

if __name__ == "__main__":

    print(
        "======================================"
    )

    print(
        "       INGRES GROQ AI TEST"
    )

    print(
        "======================================"
    )


    if client is None:

        print(
            "ERROR: GROQ_API_KEY not found."
        )

    else:

        print(
            "Groq API key loaded successfully."
        )

        print(
            "Model:",
            MODEL_NAME
        )


        test_question = (
            "Explain artificial intelligence "
            "in simple words."
        )


        print(
            "\nQuestion:",
            test_question
        )


        print(
            "\nAI Response:\n"
        )


        result = ask_groq(
            test_question
        )


        print(
            result
        )