from datetime import time

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ALLOWED_SCHEDULE_TYPES = ["daily", "weekly", "interval"]


class ScheduleTimeInput(BaseModel):
    time_of_day: time
    dose_amount: int = Field(default=1, ge=1, le=20)


class ScheduleCreate(BaseModel):
    schedule_type: str
    days_of_week: list[int] | None = None
    interval_days: int | None = Field(default=None, ge=1, le=365)
    times: list[ScheduleTimeInput] = Field(min_length=1, max_length=10)

    @field_validator("schedule_type")
    @classmethod
    def check_schedule_type(cls, value):
        # Make it lower case, then check it is in the allowed list
        value = value.strip().lower()
        if value not in ALLOWED_SCHEDULE_TYPES:
            allowed_text = ", ".join(ALLOWED_SCHEDULE_TYPES)
            raise ValueError("Schedule type must be one of: " + allowed_text)
        return value

    @model_validator(mode="after")
    def check_schedule_rules(self):
        # The same time cannot be added twice
        seen_times = []
        for item in self.times:
            if item.time_of_day in seen_times:
                raise ValueError("The same time cannot be added twice")
            seen_times.append(item.time_of_day)

        if self.schedule_type == "weekly":
            if not self.days_of_week:
                raise ValueError(
                    "Weekly schedule needs days_of_week (0 = Monday ... 6 = Sunday)"
                )
            seen_days = []
            for day in self.days_of_week:
                if day < 0 or day > 6:
                    raise ValueError("Days must be between 0 (Monday) and 6 (Sunday)")
                if day in seen_days:
                    raise ValueError("The same day cannot be added twice")
                seen_days.append(day)
            self.interval_days = None

        elif self.schedule_type == "interval":
            if self.interval_days is None:
                raise ValueError("Interval schedule needs interval_days")
            self.days_of_week = None

        else:
            # Daily schedule does not need days or interval
            self.days_of_week = None
            self.interval_days = None

        return self


class ScheduleTimeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    time_of_day: time
    dose_amount: int


class ScheduleResponse(BaseModel):
    id: int
    medication_id: int
    schedule_type: str
    days_of_week: list[int] | None
    interval_days: int | None
    times: list[ScheduleTimeResponse]