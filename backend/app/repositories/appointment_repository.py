from datetime import datetime

from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.models.appointment_model import Appointment


def get_appointment_by_id(
    db: Session, appointment_id: int, user_id: int
) -> Appointment | None:
    query = select(Appointment)
    query = query.where(Appointment.id == appointment_id)
    query = query.where(Appointment.user_id == user_id)
    return db.scalar(query)


def get_appointments(
    db: Session, user_id: int, when: str, now: datetime
) -> list[Appointment]:
    query = select(Appointment)
    query = query.where(Appointment.user_id == user_id)

    if when == "upcoming":
        query = query.where(Appointment.appointment_at >= now)
        query = query.order_by(asc(Appointment.appointment_at))
    elif when == "past":
        query = query.where(Appointment.appointment_at < now)
        query = query.order_by(desc(Appointment.appointment_at))
    else:
        query = query.order_by(asc(Appointment.appointment_at))

    result = db.scalars(query)
    return list(result)


def save_appointment(db: Session, appointment: Appointment) -> Appointment:
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def delete_appointment(db: Session, appointment: Appointment) -> None:
    db.delete(appointment)
    db.commit()