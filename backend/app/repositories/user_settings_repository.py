from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_settings_model import UserSettings


def get_settings_by_user(db: Session, user_id: int):
    query = select(UserSettings).where(UserSettings.user_id == user_id)
    return db.scalar(query)


def save_settings(db: Session, settings: UserSettings):
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def rollback(db: Session):
    db.rollback()