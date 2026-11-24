from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.medication_wizard_schema import (
    MedicationWithScheduleCreate,
    MedicationWithScheduleResponse,
)
from app.schemas.response_schema import ApiResponse
from app.services import medication_wizard_service

router = APIRouter(prefix="/medications", tags=["Medications"])


@router.post(
    "/with-schedule",
    response_model=ApiResponse[MedicationWithScheduleResponse],
    status_code=201,
)
def create_medication_with_schedule(
    data: MedicationWithScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = medication_wizard_service.create_medication_with_schedule(
        db, current_user, data
    )
    return ApiResponse(message="Medication and schedule saved successfully", data=result)