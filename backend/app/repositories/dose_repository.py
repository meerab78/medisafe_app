from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.dose_log_model import DoseLog
from app.models.medication_model import Medication
from app.models.schedule_model import Schedule, ScheduleTime


def get_active_schedules_for_day(db: Session, user_id: int, day):
    # Active medications of this user that are running on this day, with their schedules
    query = select(Medication, Schedule).select_from(Medication)
    query = query.join(Schedule, Schedule.medication_id == Medication.id)
    query = query.where(Medication.user_id == user_id)
    query = query.where(Medication.is_active.is_(True))
    query = query.where(Medication.start_date <= day)
    query = query.where(or_(Medication.end_date.is_(None), Medication.end_date >= day))
    return list(db.execute(query).all())


def get_dose_by_schedule_time_and_date(db: Session, schedule_time_id: int, day):
    query = select(DoseLog).where(
        DoseLog.schedule_time_id == schedule_time_id,
        DoseLog.scheduled_date == day,
    )
    return db.scalar(query)


def get_doses_for_day(db: Session, user_id: int, day):
    # Each row has 3 items: the dose, its medication and its schedule time (can be None)
    query = select(DoseLog, Medication, ScheduleTime).select_from(DoseLog)
    query = query.join(Medication, DoseLog.medication_id == Medication.id)
    query = query.outerjoin(ScheduleTime, DoseLog.schedule_time_id == ScheduleTime.id)
    query = query.where(Medication.user_id == user_id)
    query = query.where(Medication.is_active.is_(True))
    query = query.where(DoseLog.scheduled_date == day)
    query = query.order_by(DoseLog.scheduled_at, Medication.name)
    return list(db.execute(query).all())


def get_dose_by_id(db: Session, dose_id: int, user_id: int):
    # Finds the dose by id AND owner, so other users' doses are never found
    query = select(DoseLog).select_from(DoseLog)
    query = query.join(Medication, DoseLog.medication_id == Medication.id)
    query = query.where(DoseLog.id == dose_id)
    query = query.where(Medication.user_id == user_id)
    return db.scalar(query)


def get_schedule_time_by_id(db: Session, schedule_time_id: int):
    return db.get(ScheduleTime, schedule_time_id)


def add_dose(db: Session, dose: DoseLog):
    db.add(dose)


def save_dose(db: Session, dose: DoseLog):
    db.add(dose)
    db.commit()
    db.refresh(dose)
    return dose


def delete_pending_doses(db: Session, medication_id: int, from_date):
    # Used when a schedule changes: remove pending doses from this date onwards
    query = select(DoseLog).where(
        DoseLog.medication_id == medication_id,
        DoseLog.status == "pending",
        DoseLog.scheduled_date >= from_date,
    )
    doses = list(db.scalars(query).all())
    for dose in doses:
        db.delete(dose)
    db.flush()


def commit(db: Session):
    db.commit()


def rollback(db: Session):
    db.rollback()

def get_overdue_pending_doses(db: Session, cutoff, limit: int):
    # Pending doses whose time is before the cutoff, for active medications only
    query = select(DoseLog).select_from(DoseLog)
    query = query.join(Medication, DoseLog.medication_id == Medication.id)
    query = query.where(DoseLog.status == "pending")
    query = query.where(DoseLog.scheduled_at <= cutoff)
    query = query.where(Medication.is_active.is_(True))
    query = query.order_by(DoseLog.scheduled_at)
    query = query.limit(limit)
    return list(db.scalars(query).all())