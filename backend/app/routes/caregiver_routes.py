from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.caregiver_schema import (
    CaregiverInvite,
    CaregiverPermissionsUpdate,
    CaregiverResponse,
    InvitationResponse,
    PatientResponse,
)
from app.schemas.response_schema import ApiResponse
from app.services import caregiver_service

router = APIRouter(prefix="/caregivers", tags=["Caregivers"])


# ---------------- Patient side ----------------


@router.post("/invite", response_model=ApiResponse[CaregiverResponse], status_code=201)
def invite_caregiver(
    data: CaregiverInvite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    caregiver = caregiver_service.invite_caregiver(db, current_user, data)
    return ApiResponse(message="Invitation sent successfully", data=caregiver)


@router.get("", response_model=ApiResponse[list[CaregiverResponse]])
def list_my_caregivers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    caregivers = caregiver_service.list_my_caregivers(db, current_user)
    return ApiResponse(message="Caregivers fetched successfully", data=caregivers)


@router.put("/{link_id}/permissions", response_model=ApiResponse[CaregiverResponse])
def update_permissions(
    link_id: int,
    data: CaregiverPermissionsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    caregiver = caregiver_service.update_permissions(db, current_user, link_id, data)
    return ApiResponse(message="Permissions updated successfully", data=caregiver)


@router.delete("/{link_id}", response_model=ApiResponse)
def remove_caregiver(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    caregiver_service.remove_caregiver(db, current_user, link_id)
    return ApiResponse(message="Caregiver removed successfully")


# ---------------- Invited person side ----------------


@router.get("/invitations", response_model=ApiResponse[list[InvitationResponse]])
def list_my_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invitations = caregiver_service.list_my_invitations(db, current_user)
    return ApiResponse(message="Invitations fetched successfully", data=invitations)


@router.put(
    "/invitations/{link_id}/accept", response_model=ApiResponse[PatientResponse]
)
def accept_invitation(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = caregiver_service.accept_invitation(db, current_user, link_id)
    return ApiResponse(message="Invitation accepted", data=patient)


@router.put("/invitations/{link_id}/reject", response_model=ApiResponse)
def reject_invitation(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    caregiver_service.reject_invitation(db, current_user, link_id)
    return ApiResponse(message="Invitation rejected")


# ---------------- Caregiver side ----------------


@router.get("/patients", response_model=ApiResponse[list[PatientResponse]])
def list_my_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patients = caregiver_service.list_my_patients(db, current_user)
    return ApiResponse(message="Patients fetched successfully", data=patients)


@router.delete("/patients/{link_id}", response_model=ApiResponse)
def leave_patient(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    caregiver_service.leave_patient(db, current_user, link_id)
    return ApiResponse(message="You are no longer a caregiver for this person")