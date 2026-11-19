from datetime import time

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    medication_id: Mapped[int] = mapped_column(
        ForeignKey("medications.id", ondelete="CASCADE"), unique=True
    )
    # Allowed values: "daily", "weekly", "interval"
    schedule_type: Mapped[str] = mapped_column(String(20))
    # Weekday numbers separated by commas, Monday = 0. Example: "0,2,4"
    days_of_week: Mapped[str | None] = mapped_column(String(20))
    # Used only for "interval" type. Example: 2 means every 2 days
    interval_days: Mapped[int | None]


class ScheduleTime(Base):
    __tablename__ = "schedule_times"

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("schedules.id", ondelete="CASCADE"), index=True
    )
    time_of_day: Mapped[time]
    dose_amount: Mapped[int] = mapped_column(default=1)