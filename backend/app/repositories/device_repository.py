from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device_token_model import DeviceToken


def get_device_by_token(db: Session, fcm_token: str):
    query = select(DeviceToken).where(DeviceToken.fcm_token == fcm_token)
    return db.scalar(query)


def get_devices_by_user(db: Session, user_id: int):
    query = select(DeviceToken).where(DeviceToken.user_id == user_id)
    query = query.order_by(DeviceToken.id)
    return list(db.scalars(query).all())


def save_device(db: Session, device: DeviceToken):
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def delete_device(db: Session, device: DeviceToken):
    db.delete(device)
    db.commit()