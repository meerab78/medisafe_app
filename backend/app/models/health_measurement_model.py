from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class HealthMeasurement(Base):
    __tablename__ = "health_measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # Allowed values: "blood_pressure", "blood_glucose", "weight"
    measurement_type: Mapped[str] = mapped_column(String(30), index=True)
    # Blood pressure: systolic. Glucose and weight: the main value.
    value_1: Mapped[float]
    # Blood pressure only: diastolic. Empty for other types.
    value_2: Mapped[float | None]
    unit: Mapped[str] = mapped_column(String(20))
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)