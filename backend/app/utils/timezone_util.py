from zoneinfo import ZoneInfo


def validate_timezone_name(value: str) -> str:
    # Remove spaces from both sides
    value = value.strip()

    # Try to load the timezone. If the name is wrong, Python raises an error.
    try:
        ZoneInfo(value)
    except Exception:
        raise ValueError("Timezone is not valid. Example: Asia/Karachi")

    return value