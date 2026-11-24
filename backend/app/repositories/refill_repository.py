from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.models.medication_model import Medication
from app.models.refill_log_model import RefillLog


def get_user_medication(
    db: Session, user_id: int, medication_id: int
) -> Medication | None:
    query = select(Medication)
    query = query.where(Medication.id == medication_id)
    query = query.where(Medication.user_id == user_id)
    return db.scalar(query)


def add_refill(db: Session, medication: Medication, quantity_added: int) -> None:
    medication.stock_quantity = medication.stock_quantity + quantity_added
    refill_log = RefillLog(medication_id=medication.id, quantity_added=quantity_added)
    db.add(refill_log)
    db.commit()
    db.refresh(medication)


def set_stock(db: Session, medication: Medication, stock_quantity: int) -> None:
    medication.stock_quantity = stock_quantity
    db.commit()
    db.refresh(medication)


def get_refills_for_medication(db: Session, medication_id: int) -> list[RefillLog]:
    query = select(RefillLog)
    query = query.where(RefillLog.medication_id == medication_id)
    query = query.order_by(desc(RefillLog.refilled_at), desc(RefillLog.id))
    return list(db.scalars(query))


def get_low_stock_medications(db: Session, user_id: int) -> list[Medication]:
    query = select(Medication)
    query = query.where(Medication.user_id == user_id)
    query = query.where(Medication.is_active == True)
    query = query.where(Medication.stock_quantity <= Medication.low_stock_threshold)
    query = query.order_by(asc(Medication.stock_quantity))
    return list(db.scalars(query))