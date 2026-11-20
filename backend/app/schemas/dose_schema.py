from datetime import date, datetime, time

from pydantic import BaseModel


class DoseResponse(BaseModel):
    id: int
    medication_id: int
    medication_name: str
    dosage: str
    dose_amount: int
    scheduled_date: date
    scheduled_at: datetime
    time_of_day: time | None
    status: str
    taken_at: datetime | None


class TodayResponse(BaseModel):
    day: date
    timezone: str
    total: int
    pending: int
    taken: int
    skipped: int
    missed: int
    doses: list[DoseResponse]