from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user_model import User
from app.repositories import caregiver_repository
from app.schemas.medication_schema import MedicationResponse
from app.services import dose_service, medication_service


def get_patient_if_allowed(db: Session, caregiver: User, patient_id: int):
    # The caregiver must have an accepted link AND the permission to view medications.
    # Every failure gives the same answer, so nothing is revealed.
    link = caregiver_repository.get_accepted_link(db, caregiver.id, patient_id)
    if link is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    if not link.can_view_medications:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient = caregiver_repository.find_user_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    return patient


def get_patient_today(db: Session, caregiver: User, patient_id: int):
    patient = get_patient_if_allowed(db, caregiver, patient_id)
    # Uses the patient's own timezone, because "today" belongs to the patient
    return dose_service.get_today(db, patient)


def list_patient_medications(db: Session, caregiver: User, patient_id: int):
    patient = get_patient_if_allowed(db, caregiver, patient_id)

    # None, None, None means: only active medications, no search, no filter
    medications = medication_service.list_medications(db, patient, None, None, None)

    result = []
    for medication in medications:
        result.append(MedicationResponse.model_validate(medication))
    return result