from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.repositories import user_repository
from app.schemas.auth_schema import UserLogin
from app.schemas.user_schema import UserCreate


def register_user(db: Session, user_data: UserCreate):
    email = user_data.email.lower()

    existing_user = user_repository.get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    hashed_password = hash_password(user_data.password)
    return user_repository.create_user(
        db, user_data.full_name, email, hashed_password, user_data.timezone
    )


def login_user(db: Session, login_data: UserLogin) -> str:
    email = login_data.email.lower()
    user = user_repository.get_user_by_email(db, email)

    if user is None or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    return create_access_token(user.id)