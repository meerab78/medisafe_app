from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.appointment_schema import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
)
from app.schemas.response_schema import ApiResponse
from app.services import appointment_service

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("", response_model=ApiResponse[AppointmentResponse], status_code=201)
def create_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = appointment_service.create_appointment(db, current_user, data)
    return ApiResponse(message="Appointment saved successfully", data=appointment)


@router.get("", response_model=ApiResponse[list[AppointmentResponse]])
def list_appointments(
    when: Literal["upcoming", "past", "all"] = Query(default="upcoming"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointments = appointment_service.list_appointments(db, current_user, when)
    return ApiResponse(message="Appointments fetched successfully", data=appointments)


@router.get("/{appointment_id}", response_model=ApiResponse[AppointmentResponse])
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = appointment_service.get_appointment(db, current_user, appointment_id)
    return ApiResponse(message="Appointment fetched successfully", data=appointment)


@router.put("/{appointment_id}", response_model=ApiResponse[AppointmentResponse])
def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = appointment_service.update_appointment(
        db, current_user, appointment_id, data
    )
    return ApiResponse(message="Appointment updated successfully", data=appointment)


@router.delete("/{appointment_id}", response_model=ApiResponse)
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment_service.delete_appointment(db, current_user, appointment_id)
    return ApiResponse(message="Appointment deleted successfully")