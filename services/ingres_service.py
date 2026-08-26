import os
import json


# --------------------------------------------------
# Project paths
# --------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "ingres_data.json"
)


# --------------------------------------------------
# Load INGRES data
# --------------------------------------------------

def load_data():

    if not os.path.exists(DATA_FILE):
        return []

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return data

    except json.JSONDecodeError as error:

        print(
            "Invalid JSON in INGRES data:",
            error
        )

        return []

    except Exception as error:

        print(
            "Error loading INGRES data:",
            error
        )

        return []


# --------------------------------------------------
# Find state data
# --------------------------------------------------

def get_state_data(state):

    if not state:
        return None

    state = state.lower().strip()

    data = load_data()

    for record in data:

        record_state = record.get(
            "state",
            ""
        ).lower().strip()

        if record_state == state:

            return record

    return None


# --------------------------------------------------
# Format groundwater data
# --------------------------------------------------

def format_state_data(record):

    if not record:

        return (
            "I couldn't find groundwater data "
            "for this location in the current "
            "INGRES dataset."
        )


    state = record.get(
        "state",
        "Unknown"
    )

    year = record.get(
        "assessment_year",
        "Unknown"
    )


    recharge = record.get(
        "annual_groundwater_recharge_bcm",
        "Not available"
    )

    extractable = record.get(
        "annual_extractable_groundwater_resource_bcm",
        "Not available"
    )

    extraction = record.get(
        "annual_groundwater_extraction_bcm",
        "Not available"
    )

    stage = record.get(
        "stage_of_extraction_percent",
        "Not available"
    )


    # Assessment units

    units = record.get(
        "assessment_units",
        {}
    )

    total = units.get(
        "total",
        "Not available"
    )

    safe = units.get(
        "safe",
        "Not available"
    )

    semi_critical = units.get(
        "semi_critical",
        "Not available"
    )

    critical = units.get(
        "critical",
        "Not available"
    )

    over_exploited = units.get(
        "over_exploited",
        "Not available"
    )

    saline = units.get(
        "saline",
        "Not available"
    )


    data_status = record.get(
        "data_status",
        "Not available"
    )


    # --------------------------------------------------
    # Final response
    # --------------------------------------------------

    response = (
        f"Groundwater information for {state} "
        f"(assessment year {year}):\n\n"

        f"Annual Groundwater Recharge: "
        f"{recharge} BCM\n"

        f"Annual Extractable Groundwater "
        f"Resource: {extractable} BCM\n"

        f"Annual Groundwater Extraction: "
        f"{extraction} BCM\n"

        f"Stage of Groundwater Extraction: "
        f"{stage}%\n\n"

        f"Assessment Units: {total}\n"
        f"Safe: {safe}\n"
        f"Semi-Critical: {semi_critical}\n"
        f"Critical: {critical}\n"
        f"Over-Exploited: {over_exploited}\n"
        f"Saline: {saline}\n\n"

        f"Data note: {data_status}"
    )

    return response


# --------------------------------------------------
# Main function
# --------------------------------------------------

def get_groundwater_information(state):

    record = get_state_data(state)

    return format_state_data(record)