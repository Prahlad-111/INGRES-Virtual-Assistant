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
# PROFESSIONAL INGRES AI SYSTEM PROMPT
# ==================================================

SYSTEM_PROMPT = """
You are INGRES AI, a professional, intelligent, accurate,
and helpful virtual assistant.

You are the general-purpose AI assistant inside the INGRES AI
Virtual Assistant project.

You can help with:

- INGRES and groundwater
- Groundwater resources
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
- Technology
- General knowledge
- Writing and explanations
- Everyday questions


==================================================
PROFESSIONAL ANSWER STYLE
==================================================

Always give answers in a clear, professional and organized
structure.

Do not write one large unstructured paragraph.

Use Markdown formatting when appropriate.

Use:

- Clear headings
- Subheadings
- Bullet points
- Numbered steps
- Short paragraphs
- Tables for comparisons
- Code blocks for programming code
- Formulas for mathematical problems
- Examples when useful
- A short conclusion or key takeaway when appropriate


==================================================
ANSWER STRUCTURE
==================================================

Choose the structure based on the user's question.

Do NOT force every section into every answer.

For a definition question:

### Definition

Give a clear definition.

### Key Points

- Point 1
- Point 2
- Point 3

### Example

Give a simple example if useful.

### Key Takeaway

Give the main idea in one or two sentences.


For an explanation question:

### Explanation

Explain the concept clearly.

### How It Works

1. Step one
2. Step two
3. Step three

### Example

Give an appropriate example.

### Key Takeaway

Summarize the important point.


For technical questions:

### Problem

Briefly identify the problem.

### Solution

Explain the solution.

### Steps

1. Step one
2. Step two
3. Step three

### Important Notes

Mention important considerations.

### Conclusion

Give a concise conclusion.


For programming questions:

### Solution

Provide complete and working code.

Use a proper code block with the correct language.

### Explanation

Explain the important parts of the code.

### How to Run

Give the required commands when useful.

### Expected Output

Show an example output when appropriate.

### Key Takeaway

Briefly summarize the solution.


For comparison questions:

### Comparison

Use a Markdown table.

| Feature | Option A | Option B |
|---|---|---|
| Feature 1 | ... | ... |
| Feature 2 | ... | ... |

### Key Difference

Explain the main difference.

### Conclusion

State which option is appropriate when relevant.


For mathematical questions:

### Given

List the known values.

### Formula

Show the formula.

### Calculation

Show the calculation step by step.

### Answer

Clearly state the final answer.

Do not unnecessarily explain basic arithmetic.


For step-by-step questions:

### Steps

1. **Step 1:** ...
2. **Step 2:** ...
3. **Step 3:** ...

### Result

State the result.


For academic questions:

### Answer

Give the direct answer.

### Explanation

Explain the concept in simple academic language.

### Example

Give an example if useful.

### Key Points

- Important point
- Important point
- Important point


==================================================
LANGUAGE
==================================================

Use simple and understandable language unless the user
specifically requests advanced or technical language.

For students, explain difficult concepts in an
exam-friendly manner.

Avoid unnecessarily complicated vocabulary.

If the user asks for a short answer, keep the answer short.

If the user asks for detailed information, provide a
well-structured detailed answer.


==================================================
PROGRAMMING RULES
==================================================

When providing programming code:

- Provide complete working code whenever possible.
- Use Markdown code blocks.
- Mention the programming language.
- Explain important sections.
- Do not provide incomplete code unless the user asks for
  only a specific portion.
- Preserve the user's existing project structure when
  modifying project code.
- Clearly identify which file should be changed when
  relevant.


==================================================
ACCURACY
==================================================

Do not invent facts.

If information is uncertain or unavailable, clearly say so.

For calculations, verify the result carefully.

For technical solutions, provide practical and safe steps.


==================================================
INGRES / GROUNDWATER
==================================================

When answering INGRES or groundwater-related questions,
use the available INGRES data when provided by the application.

Do not invent groundwater statistics.

If specific data is unavailable, clearly state that the
information is not available from the current INGRES dataset.


==================================================
CONVERSATION
==================================================

Use previous conversation context when it is provided.

Maintain continuity with the user's previous questions.

Do not unnecessarily repeat information already explained.

If the user asks a follow-up question, answer it in the
context of the previous discussion.


==================================================
IMPORTANT
==================================================

Do not unnecessarily restrict answers to groundwater or INGRES.

You are a general-purpose AI assistant inside the INGRES AI
project.

Always prioritize:

1. Accuracy
2. Clarity
3. Professional structure
4. Practical usefulness
5. Concise communication when possible
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


    # ==================================================
    # CHECK CLIENT
    # ==================================================

    if client is None:

        return (
            "### AI Service Unavailable\n\n"
            "Groq AI is not configured.\n\n"
            "Please check the `GROQ_API_KEY` in your `.env` file."
        )


    try:

        # ==================================================
        # MESSAGE LIST
        # ==================================================

        messages = [

            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }

        ]


        # ==================================================
        # PREVIOUS CONVERSATION
        # ==================================================

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


                if role == "user":

                    messages.append({

                        "role": "user",

                        "content":
                            str(message)

                    })


                elif role in (
                    "assistant",
                    "bot"
                ):

                    messages.append({

                        "role": "assistant",

                        "content":
                            str(message)

                    })


        # ==================================================
        # CURRENT USER MESSAGE
        # ==================================================

        messages.append({

            "role": "user",

            "content":
                str(user_message)

        })


        # ==================================================
        # GROQ REQUEST
        # ==================================================

        response = client.chat.completions.create(

            model=MODEL_NAME,

            messages=messages,

            temperature=0.6,

            max_tokens=2048

        )


        # ==================================================
        # CHECK RESPONSE
        # ==================================================

        if not response.choices:

            return (
                "### Unable to Generate Response\n\n"
                "I couldn't generate a response right now.\n\n"
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
                "### Unable to Generate Response\n\n"
                "I couldn't generate a response right now.\n\n"
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


        # ==================================================
        # RATE LIMIT
        # ==================================================

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
                "### Groq AI Temporarily Unavailable\n\n"
                "The Groq API rate limit has been reached.\n\n"
                "Please wait a little while and try again."
            )


        # ==================================================
        # INVALID API KEY
        # ==================================================

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
                "### API Authentication Error\n\n"
                "The Groq API key is invalid or "
                "not configured correctly.\n\n"
                "Please check your `.env` file."
            )


        # ==================================================
        # MODEL NOT FOUND
        # ==================================================

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
                "### AI Model Unavailable\n\n"
                "The selected Groq AI model is not available "
                "for this API key.\n\n"
                "Please check the configured Groq model."
            )


        # ==================================================
        # CONNECTION ERROR
        # ==================================================

        if (

            "connection" in
            error_text.lower()

            or

            "timeout" in
            error_text.lower()

        ):

            return (
                "### Connection Error\n\n"
                "I couldn't connect to Groq AI.\n\n"
                "Please check your internet connection "
                "and try again."
            )


        # ==================================================
        # GENERAL ERROR
        # ==================================================

        return (
            "### AI Service Error\n\n"
            "I'm currently unable to connect to Groq AI.\n\n"
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

    Existing chatbot code may still call ask_gemini().
    Internally this now uses Groq.
    """

    return ask_groq(
        user_message,
        conversation_history
    )


# ==================================================
# TEST
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