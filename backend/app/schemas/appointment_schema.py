from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.appointment_options import APPOINTMENT_REMINDERS
from app.core.medication_options import get_option_values


class AppointmentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    doctor_name: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=200)
    # Send the time in the user's own timezone, for example 2026-12-05T16:30:00
    appointment_at: datetime
    remind_before_minutes: int | None = None
    notes: str | None = None

    @field_validator("title")
    @classmethod
    def clean_title(cls, value):
        value = value.strip()
        if value == "":
            raise ValueError("Title cannot be empty")
        return value

    @field_validator("doctor_name", "location", "notes")
    @classmethod
    def clean_optional_text(cls, value):
        if value is None:
            return None
        value = value.strip()
        if value == "":
            return None
        return value

    @field_validator("remind_before_minutes")
    @classmethod
    def check_reminder(cls, value):
        # None and 0 both mean "no reminder"
        if value is None:
            return None
        if value == 0:
            return None

        allowed_values = get_option_values(APPOINTMENT_REMINDERS)
        if value not in allowed_values:
            raise ValueError(
                "Reminder must be 30, 60, 720 or 10080 minutes, or 0 for no reminder"
            )
        return value


class AppointmentUpdate(AppointmentCreate):
    # Same fields as create. The whole appointment is replaced.
    pass


class AppointmentResponse(BaseModel):
    id: int
    title: str
    doctor_name: str | None
    location: str | None
    appointment_at: datetime
    remind_before_minutes: int | None
    notes: str | None