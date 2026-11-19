from datetime import date

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(150))
    dosage: Mapped[str] = mapped_column(String(100))
    medication_type: Mapped[str] = mapped_column(String(30))
    instructions: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date]
    end_date: Mapped[date | None]
    stock_quantity: Mapped[int] = mapped_column(default=0)
    low_stock_threshold: Mapped[int] = mapped_column(default=5)
    is_active: Mapped[bool] = mapped_column(default=True)