from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_model import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create_user(
    db: Session, full_name: str, email: str, hashed_password: str, timezone: str
) -> User:
    new_user = User(
        full_name=full_name,
        email=email,
        hashed_password=hashed_password,
        timezone=timezone,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def save_user(db: Session, user: User) -> User:
    db.commit()
    db.refresh(user)
    return user