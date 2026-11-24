from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user_model import User
from app.repositories import user_repository
from app.schemas.user_schema import ChangePasswordRequest, UserUpdate


def update_profile(db: Session, current_user: User, profile_data: UserUpdate) -> User:
    current_user.full_name = profile_data.full_name
    current_user.timezone = profile_data.timezone
    return user_repository.save_user(db, current_user)


def change_password(
    db: Session, current_user: User, password_data: ChangePasswordRequest
) -> None:
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = hash_password(password_data.new_password)
    user_repository.save_user(db, current_user)