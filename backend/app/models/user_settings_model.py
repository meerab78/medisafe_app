from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    reminders_enabled: Mapped[bool] = mapped_column(default=True)
    snooze_minutes: Mapped[int] = mapped_column(default=10)
    refill_alerts_enabled: Mapped[bool] = mapped_column(default=True)