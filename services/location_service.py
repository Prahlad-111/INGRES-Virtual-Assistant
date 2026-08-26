# --------------------------------------------------
# INGRES Location Service
# --------------------------------------------------

import re


# --------------------------------------------------
# Indian States and Union Territories
# --------------------------------------------------

INDIAN_STATES = [
    "andaman and nicobar islands",
    "andhra pradesh",
    "arunachal pradesh",
    "assam",
    "bihar",
    "chandigarh",
    "chhattisgarh",
    "dadra and nagar haveli and daman and diu",
    "delhi",
    "goa",
    "gujarat",
    "haryana",
    "himachal pradesh",
    "jammu and kashmir",
    "jharkhand",
    "karnataka",
    "kerala",
    "ladakh",
    "lakshadweep",
    "madhya pradesh",
    "maharashtra",
    "manipur",
    "meghalaya",
    "mizoram",
    "nagaland",
    "odisha",
    "puducherry",
    "punjab",
    "rajasthan",
    "sikkim",
    "tamil nadu",
    "telangana",
    "tripura",
    "uttar pradesh",
    "uttarakhand",
    "west bengal"
]


# --------------------------------------------------
# Common short forms
# --------------------------------------------------

STATE_ALIASES = {
    "wb": "west bengal",
    "west bengal": "west bengal",

    "up": "uttar pradesh",
    "uttar pradesh": "uttar pradesh",

    "mp": "madhya pradesh",
    "madhya pradesh": "madhya pradesh",

    "ap": "andhra pradesh",
    "andhra pradesh": "andhra pradesh",

    "tn": "tamil nadu",
    "tamil nadu": "tamil nadu",

    "mh": "maharashtra",
    "maharashtra": "maharashtra",

    "gj": "gujarat",
    "gujarat": "gujarat",

    "rj": "rajasthan",
    "rajasthan": "rajasthan",

    "ka": "karnataka",
    "karnataka": "karnataka",

    "kl": "kerala",
    "kerala": "kerala",

    "od": "odisha",
    "orissa": "odisha",
    "odisha": "odisha",

    "jh": "jharkhand",
    "jharkhand": "jharkhand",

    "br": "bihar",
    "bihar": "bihar",

    "pb": "punjab",
    "punjab": "punjab",

    "hr": "haryana",
    "haryana": "haryana",

    "uk": "uttarakhand",
    "uttarakhand": "uttarakhand"
}


# --------------------------------------------------
# Find state in user question
# --------------------------------------------------

def find_state(text):

    if not text:
        return None

    text = text.lower().strip()

    # Normalize punctuation
    text = re.sub(
        r"[^a-z\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )


    # Check longer names first
    sorted_states = sorted(
        STATE_ALIASES.keys(),
        key=len,
        reverse=True
    )


    for state_name in sorted_states:

        pattern = r"\b" + re.escape(
            state_name
        ) + r"\b"

        if re.search(pattern, text):

            return STATE_ALIASES[state_name]


    return None


# --------------------------------------------------
# Check whether question is requesting location data
# --------------------------------------------------

def is_location_query(text):

    if not text:
        return False


    keywords = [

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
        "stage of extraction",
        "data"

    ]


    text = text.lower()


    return any(
        keyword in text
        for keyword in keywords
    )


# --------------------------------------------------
# Create location response
# --------------------------------------------------

def get_location_response(text):

    state = find_state(text)


    if not is_location_query(text):

        return None


    if state:

        return {
            "location_found": True,
            "state": state,
            "message": (
                f"I detected the location as {state.title()}. "
                "I can use this location to retrieve "
                "INGRES groundwater assessment information."
            )
        }


    return {
        "location_found": False,
        "state": None,
        "message": (
            "Please provide a location such as a "
            "state or district so I can help with "
            "groundwater assessment information."
        )
    }