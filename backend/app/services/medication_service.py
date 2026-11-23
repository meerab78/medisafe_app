from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.medication_model import Medication
from app.models.user_model import User
from app.repositories import medication_repository
from app.schemas.medication_schema import MedicationCreate, MedicationUpdate


def create_medication(db: Session, user: User, data: MedicationCreate):
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
        start_date=data.start_date,
        end_date=data.end_date,
        stock_quantity=data.stock_quantity,
        low_stock_threshold=data.low_stock_threshold,
    )
    return medication_repository.save_medication(db, medication)


def list_medications(
    db: Session,
    user: User,
    is_active: bool | None,
    search: str | None,
    medication_type: str | None,
):
    # By default show only active medications
    if is_active is None:
        is_active = True

    if medication_type:
        medication_type = medication_type.strip().lower()

    return medication_repository.get_medications(
        db, user.id, is_active, search, medication_type
    )


def get_medication(db: Session, user: User, medication_id: int):
    medication = medication_repository.get_medication_by_id(db, medication_id, user.id)
    if medication is None:
        raise HTTPException(status_code=404, detail="Medication not found")
    return medication


def update_medication(
    db: Session, user: User, medication_id: int, data: MedicationUpdate
):
    medication = get_medication(db, user, medication_id)

    medication.name = data.name
    medication.dosage = data.dosage
    medication.medication_type = data.medication_type
    medication.route = data.route
    medication.reason = data.reason
    medication.icon = data.icon
    medication.food_instruction = data.food_instruction
    medication.instructions = data.instructions
    medication.start_date = data.start_date
    medication.end_date = data.end_date
    medication.stock_quantity = data.stock_quantity
    medication.low_stock_threshold = data.low_stock_threshold
    medication.is_active = data.is_active

    return medication_repository.save_medication(db, medication)


def delete_medication(db: Session, user: User, medication_id: int):
    # Soft delete: keep the row (and its history), only mark it inactive
    medication = get_medication(db, user, medication_id)
    medication.is_active = False
    medication_repository.save_medication(db, medication)