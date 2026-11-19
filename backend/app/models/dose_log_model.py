from datetime import date, datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DoseLog(Base):
    __tablename__ = "dose_logs"
    __table_args__ = (
        UniqueConstraint("schedule_time_id", "scheduled_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    medication_id: Mapped[int] = mapped_column(
        ForeignKey("medications.id", ondelete="CASCADE"), index=True
    )
    schedule_time_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedule_times.id", ondelete="SET NULL")
    )
    scheduled_date: Mapped[date] = mapped_column(index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Allowed values: "pending", "taken", "skipped", "missed"
    status: Mapped[str] = mapped_column(String(20), default="pending")
    taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))