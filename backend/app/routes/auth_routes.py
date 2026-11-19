from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.auth_schema import TokenResponse, UserLogin
from app.schemas.user_schema import UserCreate, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    return auth_service.register_user(db, user_data)


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    access_token = auth_service.login_user(db, login_data)
    return TokenResponse(access_token=access_token)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    # JWT is stateless, so the app deletes the token from the phone
    return {"message": "Logged out. Delete the token on the device."}