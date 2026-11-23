from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.dose_schema import TodayResponse
from app.schemas.medication_schema import MedicationResponse
from app.schemas.response_schema import ApiResponse
from app.services import caregiver_view_service

router = APIRouter(prefix="/caregivers/patients", tags=["Caregivers"])


@router.get("/{patient_id}/today", response_model=ApiResponse[TodayResponse])
def get_patient_today(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = caregiver_view_service.get_patient_today(db, current_user, patient_id)
    return ApiResponse(message="Patient's doses fetched successfully", data=today)


@router.get(
    "/{patient_id}/medications", response_model=ApiResponse[list[MedicationResponse]]
)
def get_patient_medications(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    medications = caregiver_view_service.list_patient_medications(
        db, current_user, patient_id
    )
    return ApiResponse(
        message="Patient's medications fetched successfully", data=medications
    )