from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.device_token_model import DeviceToken
from app.models.user_model import User
from app.repositories import device_repository
from app.schemas.device_schema import DeviceRegister, DeviceUnregister


def register_device(db: Session, user: User, data: DeviceRegister):
    existing = device_repository.get_device_by_token(db, data.fcm_token)

    if existing is not None:
        # The token is already saved. Give it to the current user and update the platform.
        # (The same phone may now be logged in with a different account.)
        existing.user_id = user.id
        existing.platform = data.platform
        return device_repository.save_device(db, existing)

    device = DeviceToken(
        user_id=user.id,
        fcm_token=data.fcm_token,
        platform=data.platform,
    )
    return device_repository.save_device(db, device)


def list_devices(db: Session, user: User):
    return device_repository.get_devices_by_user(db, user.id)


def unregister_device(db: Session, user: User, data: DeviceUnregister):
    device = device_repository.get_device_by_token(db, data.fcm_token)

    # If the token does not exist or belongs to someone else, show the same message
    if device is None or device.user_id != user.id:
        raise HTTPException(status_code=404, detail="Device not found")

    device_repository.delete_device(db, device)