from datetime import date

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.dose_log_model import DoseLog
from app.models.medication_model import Medication


def get_dose_rows_in_range(
    db: Session,
    user_id: int,
    start_date: date,
    end_date: date,
    medication_id: int | None = None,
):
    query = select(DoseLog, Medication.name)
    query = query.join(Medication, DoseLog.medication_id == Medication.id)
    query = query.where(Medication.user_id == user_id)
    query = query.where(DoseLog.scheduled_date >= start_date)
    query = query.where(DoseLog.scheduled_date <= end_date)
    if medication_id is not None:
        query = query.where(DoseLog.medication_id == medication_id)
    query = query.order_by(desc(DoseLog.scheduled_at))

    result = db.execute(query)
    return result.all()