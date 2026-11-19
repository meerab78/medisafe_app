from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.medication_model import Medication


def save_medication(db: Session, medication: Medication):
    db.add(medication)
    db.commit()
    db.refresh(medication)
    return medication


def get_medication_by_id(db: Session, medication_id: int, user_id: int):
    # Looks for the medication by id AND owner, so other users' data is never found
    query = select(Medication).where(
        Medication.id == medication_id,
        Medication.user_id == user_id,
    )
    return db.scalar(query)


def get_medications(
    db: Session,
    user_id: int,
    is_active: bool,
    search: str | None,
    medication_type: str | None,
):
    query = select(Medication).where(Medication.user_id == user_id)
    query = query.where(Medication.is_active == is_active)

    if search:
        query = query.where(Medication.name.ilike("%" + search + "%"))

    if medication_type:
        query = query.where(Medication.medication_type == medication_type)

    query = query.order_by(Medication.name)
    result = db.scalars(query).all()
    return list(result)