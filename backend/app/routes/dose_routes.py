from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.dose_schema import DoseResponse, TodayResponse
from app.schemas.response_schema import ApiResponse
from app.services import dose_service

router = APIRouter(prefix="/doses", tags=["Doses"])


@router.get("/today", response_model=ApiResponse[TodayResponse])
def get_today_doses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = dose_service.get_today(db, current_user)
    return ApiResponse(message="Today's doses fetched successfully", data=today)


@router.put("/{dose_id}/take", response_model=ApiResponse[DoseResponse])
def take_dose(
    dose_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dose = dose_service.mark_dose(db, current_user, dose_id, "taken")
    return ApiResponse(message="Dose marked as taken", data=dose)


@router.put("/{dose_id}/skip", response_model=ApiResponse[DoseResponse])
def skip_dose(
    dose_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dose = dose_service.mark_dose(db, current_user, dose_id, "skipped")
    return ApiResponse(message="Dose marked as skipped", data=dose)