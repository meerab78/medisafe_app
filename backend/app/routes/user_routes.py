from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.response_schema import ApiResponse
from app.schemas.user_schema import ChangePasswordRequest, UserResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=ApiResponse[UserResponse])
def get_my_profile(current_user: User = Depends(get_current_user)):
    return ApiResponse(
        message="Profile fetched successfully",
        data=UserResponse.model_validate(current_user),
    )


@router.put("/me", response_model=ApiResponse[UserResponse])
def update_my_profile(
    profile_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = user_service.update_profile(db, current_user, profile_data)
    return ApiResponse(
        message="Profile updated successfully",
        data=UserResponse.model_validate(user),
    )


@router.put("/me/password", response_model=ApiResponse)
def change_my_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_service.change_password(db, current_user, password_data)
    return ApiResponse(message="Password changed successfully")