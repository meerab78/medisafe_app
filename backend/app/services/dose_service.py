from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.dose_log_model import DoseLog
from app.models.user_model import User
from app.repositories import dose_repository, medication_repository, schedule_repository
from app.schemas.dose_schema import DoseResponse, TodayResponse
from app.services import schedule_service
from app.utils.timezone_util import get_today_for_timezone, get_zone


def schedule_runs_on_day(schedule, medication, day):
    if schedule.schedule_type == "daily":
        return True

    if schedule.schedule_type == "weekly":
        days = schedule_service.days_text_to_list(schedule.days_of_week)
        if days is None:
            return False
        # weekday() gives Monday = 0 ... Sunday = 6
        return day.weekday() in days

    if schedule.schedule_type == "interval":
        if schedule.interval_days is None:
            return False
        # Count days from the start date of the medication
        gap = (day - medication.start_date).days
        return gap % schedule.interval_days == 0

    return False


def generate_doses_for_day(db: Session, user: User, day):
    zone = get_zone(user.timezone)
    rows = dose_repository.get_active_schedules_for_day(db, user.id, day)

    for row in rows:
        medication = row[0]
        schedule = row[1]

        if not schedule_runs_on_day(schedule, medication, day):
            continue

        times = schedule_repository.get_times_by_schedule(db, schedule.id)
        for schedule_time in times:
            existing = dose_repository.get_dose_by_schedule_time_and_date(
                db, schedule_time.id, day
            )
            if existing is not None:
                continue

            # Combine the date and the time in the user's own timezone
            scheduled_at = datetime.combine(day, schedule_time.time_of_day, tzinfo=zone)
            dose = DoseLog(
                medication_id=medication.id,
                schedule_time_id=schedule_time.id,
                scheduled_date=day,
                scheduled_at=scheduled_at,
                status="pending",
            )
            dose_repository.add_dose(db, dose)

    try:
        dose_repository.commit(db)
    except IntegrityError:
        # Another request created the same dose at the same moment, so we ignore it
        dose_repository.rollback(db)


def make_dose_response(dose, medication, schedule_time):
    # A dose can have no schedule time if the schedule was changed later
    if schedule_time is None:
        time_of_day = None
        dose_amount = 1
    else:
        time_of_day = schedule_time.time_of_day
        dose_amount = schedule_time.dose_amount

    return DoseResponse(
        id=dose.id,
        medication_id=medication.id,
        medication_name=medication.name,
        dosage=medication.dosage,
        dose_amount=dose_amount,
        scheduled_date=dose.scheduled_date,
        scheduled_at=dose.scheduled_at,
        time_of_day=time_of_day,
        status=dose.status,
        taken_at=dose.taken_at,
    )


def get_today(db: Session, user: User):
    today = get_today_for_timezone(user.timezone)

    # Create today's doses if they do not exist yet
    generate_doses_for_day(db, user, today)

    rows = dose_repository.get_doses_for_day(db, user.id, today)

    doses = []
    pending = 0
    taken = 0
    skipped = 0
    missed = 0

    for row in rows:
        dose = row[0]
        medication = row[1]
        schedule_time = row[2]
        doses.append(make_dose_response(dose, medication, schedule_time))

        if dose.status == "pending":
            pending = pending + 1
        elif dose.status == "taken":
            taken = taken + 1
        elif dose.status == "skipped":
            skipped = skipped + 1
        elif dose.status == "missed":
            missed = missed + 1

    return TodayResponse(
        day=today,
        timezone=user.timezone,
        total=len(doses),
        pending=pending,
        taken=taken,
        skipped=skipped,
        missed=missed,
        doses=doses,
    )


def mark_dose(db: Session, user: User, dose_id: int, new_status: str):
    dose = dose_repository.get_dose_by_id(db, dose_id, user.id)
    if dose is None:
        raise HTTPException(status_code=404, detail="Dose not found")

    if dose.status == "taken" or dose.status == "skipped":
        raise HTTPException(
            status_code=400,
            detail="This dose is already marked as " + dose.status,
        )

    dose.status = new_status
    if new_status == "taken":
        dose.taken_at = datetime.now(timezone.utc)

    dose = dose_repository.save_dose(db, dose)

    medication = medication_repository.get_medication_by_id(
        db, dose.medication_id, user.id
    )
    schedule_time = None
    if dose.schedule_time_id is not None:
        schedule_time = dose_repository.get_schedule_time_by_id(
            db, dose.schedule_time_id
        )

    return make_dose_response(dose, medication, schedule_time)