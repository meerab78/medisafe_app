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
    # Only used when the form is "other". Example: "ears", "nose"
    route: Mapped[str | None] = mapped_column(String(20))
    # What the user takes it for (optional)
    reason: Mapped[str | None] = mapped_column(String(200))
    # Icon name chosen in the app (optional)
    icon: Mapped[str | None] = mapped_column(String(30))
    # Allowed values: "before_meal", "with_meal", "after_meal", "any"
    food_instruction: Mapped[str] = mapped_column(
        String(20), default="any", server_default="any"
    )
    instructions: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date]
    end_date: Mapped[date | None]
    stock_quantity: Mapped[int] = mapped_column(default=0)
    low_stock_threshold: Mapped[int] = mapped_column(default=5)
    is_active: Mapped[bool] = mapped_column(default=True)