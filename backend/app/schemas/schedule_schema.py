from datetime import time

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ALLOWED_SCHEDULE_TYPES = ["daily", "weekly", "interval"]

# A day has 24 hours, so there cannot be more than 24 times
MAX_TIMES_PER_DAY = 24


class ScheduleTimeInput(BaseModel):
    time_of_day: time
    dose_amount: int = Field(default=1, ge=1, le=20)


def make_hourly_times(first_time, hours_between):
    # Example: first time 06:00 and every 8 hours gives 06:00, 14:00, 22:00
    times = []
    minutes = first_time.hour * 60 + first_time.minute
    gap = hours_between * 60

    # Stop when we reach the end of the day
    while minutes < 24 * 60:
        hour = minutes // 60
        minute = minutes % 60
        item = ScheduleTimeInput(time_of_day=time(hour, minute), dose_amount=1)
        times.append(item)
        minutes = minutes + gap

    return times


class ScheduleCreate(BaseModel):
    schedule_type: str
    days_of_week: list[int] | None = None
    interval_days: int | None = Field(default=None, ge=1, le=365)
    # Send either "times", or "hours_between" together with "first_dose_time"
    times: list[ScheduleTimeInput] | None = None
    hours_between: int | None = Field(default=None, ge=1, le=24)
    first_dose_time: time | None = None

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
        # Step 1: decide the times
        if self.hours_between is not None:
            if self.times:
                raise ValueError("Send either times or hours_between, not both")
            if self.first_dose_time is None:
                raise ValueError("first_dose_time is required with hours_between")
            self.times = make_hourly_times(self.first_dose_time, self.hours_between)
        else:
            if not self.times:
                raise ValueError("Add at least one time, or use hours_between")

        if len(self.times) > MAX_TIMES_PER_DAY:
            raise ValueError("A schedule can have at most 24 times")

        # Step 2: the same time cannot be added twice
        seen_times = []
        for item in self.times:
            if item.time_of_day in seen_times:
                raise ValueError("The same time cannot be added twice")
            seen_times.append(item.time_of_day)

        # Step 3: rules for each schedule type
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