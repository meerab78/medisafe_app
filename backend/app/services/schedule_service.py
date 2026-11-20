from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.schedule_model import Schedule, ScheduleTime
from app.models.user_model import User
from app.repositories import schedule_repository
from app.schemas.schedule_schema import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleTimeResponse,
)
from app.services import medication_service


def days_list_to_text(days):
    # [4, 0, 2] becomes "0,2,4"
    if days is None:
        return None
    sorted_days = sorted(days)
    parts = []
    for day in sorted_days:
        parts.append(str(day))
    return ",".join(parts)


def days_text_to_list(text):
    # "0,2,4" becomes [0, 2, 4]
    if text is None or text == "":
        return None
    days = []
    for part in text.split(","):
        days.append(int(part))
    return days


def build_schedule_response(db: Session, schedule: Schedule):
    times = schedule_repository.get_times_by_schedule(db, schedule.id)

    time_responses = []
    for schedule_time in times:
        time_responses.append(ScheduleTimeResponse.model_validate(schedule_time))

    return ScheduleResponse(
        id=schedule.id,
        medication_id=schedule.medication_id,
        schedule_type=schedule.schedule_type,
        days_of_week=days_text_to_list(schedule.days_of_week),
        interval_days=schedule.interval_days,
        times=time_responses,
    )


def save_times(db: Session, schedule_id: int, times):
    for item in times:
        schedule_time = ScheduleTime(
            schedule_id=schedule_id,
            time_of_day=item.time_of_day,
            dose_amount=item.dose_amount,
        )
        schedule_repository.add_schedule_time(db, schedule_time)


def get_schedule_or_404(db: Session, medication_id: int):
    schedule = schedule_repository.get_schedule_by_medication(db, medication_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


def create_schedule(
    db: Session, user: User, medication_id: int, data: ScheduleCreate
):
    # This raises 404 if the medication is not found or belongs to someone else
    medication = medication_service.get_medication(db, user, medication_id)

    existing = schedule_repository.get_schedule_by_medication(db, medication.id)
    if existing is not None:
        raise HTTPException(
            status_code=409, detail="This medication already has a schedule"
        )

    schedule = Schedule(
        medication_id=medication.id,
        schedule_type=data.schedule_type,
        days_of_week=days_list_to_text(data.days_of_week),
        interval_days=data.interval_days,
    )
    schedule_repository.add_schedule(db, schedule)
    save_times(db, schedule.id, data.times)
    schedule_repository.commit(db)

    return build_schedule_response(db, schedule)


def get_schedule(db: Session, user: User, medication_id: int):
    medication = medication_service.get_medication(db, user, medication_id)
    schedule = get_schedule_or_404(db, medication.id)
    return build_schedule_response(db, schedule)


def update_schedule(
    db: Session, user: User, medication_id: int, data: ScheduleCreate
):
    medication = medication_service.get_medication(db, user, medication_id)
    schedule = get_schedule_or_404(db, medication.id)

    schedule.schedule_type = data.schedule_type
    schedule.days_of_week = days_list_to_text(data.days_of_week)
    schedule.interval_days = data.interval_days

    # Replace all old times with the new ones
    schedule_repository.delete_times_by_schedule(db, schedule.id)
    save_times(db, schedule.id, data.times)
    schedule_repository.commit(db)

    return build_schedule_response(db, schedule)


def delete_schedule(db: Session, user: User, medication_id: int):
    medication = medication_service.get_medication(db, user, medication_id)
    schedule = get_schedule_or_404(db, medication.id)

    # Delete the times first, then the schedule itself
    schedule_repository.delete_times_by_schedule(db, schedule.id)
    schedule_repository.delete_schedule(db, schedule)
    schedule_repository.commit(db)