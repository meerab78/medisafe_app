from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CaregiverLink(Base):
    __tablename__ = "caregiver_links"
    __table_args__ = (
        UniqueConstraint("patient_id", "invited_email"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # Empty until the invited person has an account and accepts
    caregiver_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    invited_email: Mapped[str] = mapped_column(String(255))
    # Allowed values: "pending", "accepted", "rejected"
    status: Mapped[str] = mapped_column(String(20), default="pending")
    can_view_medications: Mapped[bool] = mapped_column(default=True)
    can_view_health: Mapped[bool] = mapped_column(default=False)
    receive_missed_alerts: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )