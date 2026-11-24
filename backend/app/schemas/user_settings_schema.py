from pydantic import BaseModel, field_validator

from app.core.user_settings_options import SNOOZE_OPTIONS


class UserSettingsUpdate(BaseModel):
    reminders_enabled: bool
    snooze_minutes: int
    refill_alerts_enabled: bool

    @field_validator("snooze_minutes")
    @classmethod
    def check_snooze_minutes(cls, value):
        if value not in SNOOZE_OPTIONS:
            texts = []
            for option in SNOOZE_OPTIONS:
                texts.append(str(option))
            raise ValueError("Snooze minutes must be one of: " + ", ".join(texts))
        return value


class UserSettingsResponse(BaseModel):
    reminders_enabled: bool
    snooze_minutes: int
    refill_alerts_enabled: bool
    # The app uses this list to build its snooze dropdown
    snooze_options: list[int]