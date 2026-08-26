import json
import os


# Project root
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


# Dataset path
DATASET_PATH = os.path.join(
    BASE_DIR,
    "dataset",
    "intents.json"
)


def load_responses():
    """
    Load chatbot responses from intents.json.
    """

    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    response_data = {}

    for intent in data["intents"]:
        response_data[intent["tag"]] = intent["responses"]

    return response_data


# Load responses when module starts
responses = load_responses()


def get_responses(intent):
    """
    Return responses for a given intent.
    """

    return responses.get(
        intent,
        ["I'm sorry, I don't have an answer for that."]
    )