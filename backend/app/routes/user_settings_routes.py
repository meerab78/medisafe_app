from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.response_schema import ApiResponse
from app.schemas.user_settings_schema import UserSettingsResponse, UserSettingsUpdate
from app.services import user_settings_service

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=ApiResponse[UserSettingsResponse])
def get_my_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = user_settings_service.get_settings(db, current_user)
    return ApiResponse(message="Settings fetched successfully", data=settings)


@router.put("", response_model=ApiResponse[UserSettingsResponse])
def update_my_settings(
    data: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = user_settings_service.update_settings(db, current_user, data)
    return ApiResponse(message="Settings updated successfully", data=settings)