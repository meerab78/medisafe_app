from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.medication_model import Medication
from app.models.schedule_model import Schedule
from app.models.user_model import User
from app.repositories import medication_repository, schedule_repository
from app.schemas.medication_schema import MedicationResponse
from app.schemas.medication_wizard_schema import (
    MedicationWithScheduleCreate,
    MedicationWithScheduleResponse,
)
from app.services import schedule_service
from app.utils.timezone_util import get_today_for_timezone


def create_medication_with_schedule(
    db: Session, user: User, data: MedicationWithScheduleCreate
):
    # If the wizard did not send a start date, use today in the user's timezone
    start_date = data.start_date
    if start_date is None:
        start_date = get_today_for_timezone(user.timezone)

    if data.end_date is not None:
        if data.end_date < start_date:
            raise HTTPException(
                status_code=400, detail="End date cannot be before start date"
            )

    medication = Medication(
        user_id=user.id,
        name=data.name,
        dosage=data.dosage,
        medication_type=data.medication_type,
        route=data.route,
        reason=data.reason,
        icon=data.icon,
        food_instruction=data.food_instruction,
        instructions=data.instructions,
        start_date=start_date,
        end_date=data.end_date,
        stock_quantity=data.stock_quantity,
        low_stock_threshold=data.low_stock_threshold,
    )
    medication_repository.add_medication(db, medication)

    schedule_data = data.schedule
    schedule = Schedule(
        medication_id=medication.id,
        schedule_type=schedule_data.schedule_type,
        days_of_week=schedule_service.days_list_to_text(schedule_data.days_of_week),
        interval_days=schedule_data.interval_days,
    )
    schedule_repository.add_schedule(db, schedule)
    schedule_service.save_times(db, schedule.id, schedule_data.times)

    # One commit saves the medication, the schedule and the times together
    schedule_repository.commit(db)

    schedule_response = schedule_service.build_schedule_response(db, schedule)
    medication_response = MedicationResponse.model_validate(medication)

    return MedicationWithScheduleResponse(
        medication=medication_response,
        schedule=schedule_response,
    )