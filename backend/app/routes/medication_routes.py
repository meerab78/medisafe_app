from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.medication_schema import (
    MedicationCreate,
    MedicationResponse,
    MedicationUpdate,
)
from app.schemas.response_schema import ApiResponse
from app.services import medication_service

router = APIRouter(prefix="/medications", tags=["Medications"])


@router.post("", response_model=ApiResponse[MedicationResponse], status_code=201)
def create_medication(
    data: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    medication = medication_service.create_medication(db, current_user, data)
    return ApiResponse(
        message="Medication added successfully",
        data=MedicationResponse.model_validate(medication),
    )


@router.get("", response_model=ApiResponse[list[MedicationResponse]])
def list_medications(
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    medication_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    medications = medication_service.list_medications(
        db, current_user, is_active, search, medication_type
    )

    result = []
    for medication in medications:
        result.append(MedicationResponse.model_validate(medication))

    return ApiResponse(message="Medications fetched successfully", data=result)


@router.get("/{medication_id}", response_model=ApiResponse[MedicationResponse])
def get_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    medication = medication_service.get_medication(db, current_user, medication_id)
    return ApiResponse(
        message="Medication fetched successfully",
        data=MedicationResponse.model_validate(medication),
    )


@router.put("/{medication_id}", response_model=ApiResponse[MedicationResponse])
def update_medication(
    medication_id: int,
    data: MedicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    medication = medication_service.update_medication(
        db, current_user, medication_id, data
    )
    return ApiResponse(
        message="Medication updated successfully",
        data=MedicationResponse.model_validate(medication),
    )


@router.delete("/{medication_id}", response_model=ApiResponse)
def delete_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    medication_service.delete_medication(db, current_user, medication_id)
    return ApiResponse(message="Medication deleted successfully")