from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.appointment_model import Appointment
from app.models.user_model import User
from app.repositories import appointment_repository
from app.schemas.appointment_schema import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
)
from app.utils.timezone_util import get_zone


def to_utc(value, user: User):
    # A time without timezone is treated as the user's own local time
    if value.tzinfo is None:
        value = value.replace(tzinfo=get_zone(user.timezone))
    return value.astimezone(timezone.utc)


def make_response(appointment: Appointment, user: User):
    stored_time = appointment.appointment_at
    # Some databases (like SQLite in tests) give back a time without timezone.
    # We always save UTC, so it is safe to treat it as UTC.
    if stored_time.tzinfo is None:
        stored_time = stored_time.replace(tzinfo=timezone.utc)

    # Show the time in the user's own timezone
    local_time = stored_time.astimezone(get_zone(user.timezone))

    return AppointmentResponse(
        id=appointment.id,
        title=appointment.title,
        doctor_name=appointment.doctor_name,
        location=appointment.location,
        appointment_at=local_time,
        remind_before_minutes=appointment.remind_before_minutes,
        notes=appointment.notes,
    )


def get_appointment_or_404(db: Session, user: User, appointment_id: int):
    appointment = appointment_repository.get_appointment_by_id(
        db, appointment_id, user.id
    )
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


def create_appointment(db: Session, user: User, data: AppointmentCreate):
    appointment_time = to_utc(data.appointment_at, user)

    now = datetime.now(timezone.utc)
    if appointment_time <= now:
        raise HTTPException(
            status_code=400, detail="Appointment time must be in the future"
        )

    appointment = Appointment(
        user_id=user.id,
        title=data.title,
        doctor_name=data.doctor_name,
        location=data.location,
        appointment_at=appointment_time,
        remind_before_minutes=data.remind_before_minutes,
        notes=data.notes,
    )
    saved = appointment_repository.save_appointment(db, appointment)
    return make_response(saved, user)


def list_appointments(db: Session, user: User, when: str):
    now = datetime.now(timezone.utc)
    appointments = appointment_repository.get_appointments(db, user.id, when, now)

    result = []
    for appointment in appointments:
        result.append(make_response(appointment, user))
    return result


def get_appointment(db: Session, user: User, appointment_id: int):
    appointment = get_appointment_or_404(db, user, appointment_id)
    return make_response(appointment, user)


def update_appointment(
    db: Session, user: User, appointment_id: int, data: AppointmentUpdate
):
    appointment = get_appointment_or_404(db, user, appointment_id)

    appointment.title = data.title
    appointment.doctor_name = data.doctor_name
    appointment.location = data.location
    appointment.appointment_at = to_utc(data.appointment_at, user)
    appointment.remind_before_minutes = data.remind_before_minutes
    appointment.notes = data.notes

    saved = appointment_repository.save_appointment(db, appointment)
    return make_response(saved, user)


def delete_appointment(db: Session, user: User, appointment_id: int):
    appointment = get_appointment_or_404(db, user, appointment_id)
    appointment_repository.delete_appointment(db, appointment)