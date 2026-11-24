from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(150))
    doctor_name: Mapped[str | None] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(200))
    appointment_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True
    )
    # Minutes before the appointment. None means no reminder.
    remind_before_minutes: Mapped[int | None]
    notes: Mapped[str | None] = mapped_column(Text)