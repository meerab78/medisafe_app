from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RefillLog(Base):
    __tablename__ = "refill_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    medication_id: Mapped[int] = mapped_column(
        ForeignKey("medications.id", ondelete="CASCADE"), index=True
    )
    quantity_added: Mapped[int]
    refilled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )