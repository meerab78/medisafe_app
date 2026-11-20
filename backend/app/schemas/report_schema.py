from datetime import date, datetime

from pydantic import BaseModel


class HistoryDoseItem(BaseModel):
    id: int
    medication_id: int
    medication_name: str
    scheduled_date: date
    scheduled_at: datetime
    status: str
    taken_at: datetime | None


class HistoryResponse(BaseModel):
    start_date: date
    end_date: date
    total: int
    doses: list[HistoryDoseItem]


class DayStats(BaseModel):
    day: date
    taken: int
    skipped: int
    missed: int
    pending: int
    total: int


class AdherenceReport(BaseModel):
    period: str
    start_date: date
    end_date: date
    taken: int
    skipped: int
    missed: int
    pending: int
    total: int
    adherence_percent: float | None
    days: list[DayStats]