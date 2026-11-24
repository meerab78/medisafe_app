from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.auth_schema import TokenResponse, UserLogin
from app.schemas.response_schema import ApiResponse
from app.schemas.user_schema import UserCreate, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    user = auth_service.register_user(db, user_data)
    return ApiResponse(
        message="Account created successfully",
        data=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    access_token = auth_service.login_user(db, login_data)
    return ApiResponse(
        message="Login successful",
        data=TokenResponse(access_token=access_token),
    )


@router.post("/logout", response_model=ApiResponse)
def logout(current_user: User = Depends(get_current_user)):
    # JWT is stateless, so the app deletes the token from the phone
    return ApiResponse(message="Logged out successfully")