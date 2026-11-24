from datetime import date

from pydantic import BaseModel

from app.schemas.medication_schema import MedicationCreate, MedicationResponse
from app.schemas.schedule_schema import ScheduleCreate, ScheduleResponse


class MedicationWithScheduleCreate(MedicationCreate):
    # The wizard may leave the start date empty. The server then uses today's date.
    start_date: date | None = None
    schedule: ScheduleCreate


class MedicationWithScheduleResponse(BaseModel):
    medication: MedicationResponse
    schedule: ScheduleResponse