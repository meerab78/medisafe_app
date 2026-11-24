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

def list_fcm_tokens_for_user(db: Session, user_id: int) -> list[str]:
    tokens = db.scalars(
        select(DeviceToken.fcm_token).where(DeviceToken.user_id == user_id)
    )
    return list(tokens)


def remove_fcm_token(db: Session, fcm_token: str) -> None:
    device = db.scalar(select(DeviceToken).where(DeviceToken.fcm_token == fcm_token))
    if device is not None:
        db.delete(device)
        db.commit()