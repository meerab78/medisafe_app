from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.response_schema import ApiResponse
from app.schemas.schedule_schema import ScheduleCreate, ScheduleResponse
from app.services import schedule_service

router = APIRouter(prefix="/medications", tags=["Schedules"])


@router.post(
    "/{medication_id}/schedule",
    response_model=ApiResponse[ScheduleResponse],
    status_code=201,
)
def create_schedule(
    medication_id: int,
    data: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schedule = schedule_service.create_schedule(db, current_user, medication_id, data)
    return ApiResponse(message="Schedule created successfully", data=schedule)


@router.get("/{medication_id}/schedule", response_model=ApiResponse[ScheduleResponse])
def get_schedule(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schedule = schedule_service.get_schedule(db, current_user, medication_id)
    return ApiResponse(message="Schedule fetched successfully", data=schedule)


@router.put("/{medication_id}/schedule", response_model=ApiResponse[ScheduleResponse])
def update_schedule(
    medication_id: int,
    data: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schedule = schedule_service.update_schedule(db, current_user, medication_id, data)
    return ApiResponse(message="Schedule updated successfully", data=schedule)


@router.delete("/{medication_id}/schedule", response_model=ApiResponse)
def delete_schedule(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schedule_service.delete_schedule(db, current_user, medication_id)
    return ApiResponse(message="Schedule deleted successfully")