from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.device_schema import DeviceRegister, DeviceResponse, DeviceUnregister
from app.schemas.response_schema import ApiResponse
from app.services import device_service

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post("", response_model=ApiResponse[DeviceResponse])
def register_device(
    data: DeviceRegister,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = device_service.register_device(db, current_user, data)
    return ApiResponse(
        message="Device registered successfully",
        data=DeviceResponse.model_validate(device),
    )


@router.get("", response_model=ApiResponse[list[DeviceResponse]])
def list_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    devices = device_service.list_devices(db, current_user)

    result = []
    for device in devices:
        result.append(DeviceResponse.model_validate(device))

    return ApiResponse(message="Devices fetched successfully", data=result)


@router.post("/unregister", response_model=ApiResponse)
def unregister_device(
    data: DeviceUnregister,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device_service.unregister_device(db, current_user, data)
    return ApiResponse(message="Device removed successfully")