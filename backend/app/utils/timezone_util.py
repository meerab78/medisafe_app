from datetime import datetime, timezone
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


def get_zone(timezone_name: str):
    # Returns the timezone object. If the saved name is broken, use UTC.
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return timezone.utc


def get_today_for_timezone(timezone_name: str):
    # Today's date for the user's own timezone
    zone = get_zone(timezone_name)
    return datetime.now(zone).date()