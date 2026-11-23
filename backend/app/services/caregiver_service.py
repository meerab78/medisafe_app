from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.caregiver_options import MAX_CAREGIVERS_PER_PATIENT
from app.models.caregiver_link_model import CaregiverLink
from app.models.user_model import User
from app.repositories import caregiver_repository
from app.schemas.caregiver_schema import (
    CaregiverInvite,
    CaregiverPermissionsUpdate,
    CaregiverResponse,
    InvitationResponse,
    PatientResponse,
)


def make_caregiver_response(db: Session, link: CaregiverLink):
    # Find the caregiver's name if that email already has an account
    caregiver = caregiver_repository.find_user_by_email(db, link.invited_email)
    caregiver_name = None
    if caregiver is not None:
        caregiver_name = caregiver.full_name

    return CaregiverResponse(
        id=link.id,
        email=link.invited_email,
        caregiver_name=caregiver_name,
        status=link.status,
        can_view_medications=link.can_view_medications,
        can_view_health=link.can_view_health,
        receive_missed_alerts=link.receive_missed_alerts,
        created_at=link.created_at,
    )


def make_patient_response(db: Session, link: CaregiverLink):
    patient = caregiver_repository.find_user_by_id(db, link.patient_id)

    return PatientResponse(
        id=link.id,
        patient_id=link.patient_id,
        patient_name=patient.full_name,
        patient_email=patient.email,
        status=link.status,
        can_view_medications=link.can_view_medications,
        can_view_health=link.can_view_health,
        receive_missed_alerts=link.receive_missed_alerts,
        created_at=link.created_at,
    )


def make_invitation_response(db: Session, link: CaregiverLink):
    patient = caregiver_repository.find_user_by_id(db, link.patient_id)

    return InvitationResponse(
        id=link.id,
        patient_name=patient.full_name,
        patient_email=patient.email,
        can_view_medications=link.can_view_medications,
        can_view_health=link.can_view_health,
        receive_missed_alerts=link.receive_missed_alerts,
        created_at=link.created_at,
    )


# ---------------- Patient side ----------------


def invite_caregiver(db: Session, user: User, data: CaregiverInvite):
    email = data.email.strip().lower()

    if email == user.email.lower():
        raise HTTPException(status_code=400, detail="You cannot invite yourself")

    existing = caregiver_repository.get_link_by_patient_and_email(db, user.id, email)
    if existing is not None:
        if existing.status == "pending":
            raise HTTPException(
                status_code=409, detail="You have already invited this person"
            )
        if existing.status == "accepted":
            raise HTTPException(
                status_code=409, detail="This person is already your caregiver"
            )

    # Count the caregivers this patient already has (pending and accepted)
    active_links = caregiver_repository.get_active_links_by_patient(db, user.id)
    if len(active_links) >= MAX_CAREGIVERS_PER_PATIENT:
        raise HTTPException(
            status_code=400,
            detail="You can have at most "
            + str(MAX_CAREGIVERS_PER_PATIENT)
            + " caregivers",
        )

    if existing is not None:
        # The old invitation was rejected, so we send it again
        link = existing
        link.caregiver_id = None
        link.status = "pending"
    else:
        link = CaregiverLink(patient_id=user.id, invited_email=email)

    link.can_view_medications = data.can_view_medications
    link.can_view_health = data.can_view_health
    link.receive_missed_alerts = data.receive_missed_alerts

    saved = caregiver_repository.save_link(db, link)
    return make_caregiver_response(db, saved)


def list_my_caregivers(db: Session, user: User):
    links = caregiver_repository.get_active_links_by_patient(db, user.id)

    result = []
    for link in links:
        result.append(make_caregiver_response(db, link))
    return result


def update_permissions(
    db: Session, user: User, link_id: int, data: CaregiverPermissionsUpdate
):
    link = caregiver_repository.get_link_by_id(db, link_id)

    # Only the patient who owns the link can change permissions
    if link is None or link.patient_id != user.id or link.status == "rejected":
        raise HTTPException(status_code=404, detail="Caregiver not found")

    link.can_view_medications = data.can_view_medications
    link.can_view_health = data.can_view_health
    link.receive_missed_alerts = data.receive_missed_alerts

    saved = caregiver_repository.save_link(db, link)
    return make_caregiver_response(db, saved)


def remove_caregiver(db: Session, user: User, link_id: int):
    link = caregiver_repository.get_link_by_id(db, link_id)

    if link is None or link.patient_id != user.id:
        raise HTTPException(status_code=404, detail="Caregiver not found")

    caregiver_repository.delete_link(db, link)


# ---------------- Invited person side ----------------


def get_invitation_or_404(db: Session, user: User, link_id: int):
    link = caregiver_repository.get_link_by_id(db, link_id)

    # The invitation must be pending and sent to this user's email
    if link is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if link.status != "pending":
        raise HTTPException(status_code=404, detail="Invitation not found")
    if link.invited_email != user.email.lower():
        raise HTTPException(status_code=404, detail="Invitation not found")

    return link


def list_my_invitations(db: Session, user: User):
    links = caregiver_repository.get_pending_invitations_by_email(
        db, user.email.lower()
    )

    result = []
    for link in links:
        result.append(make_invitation_response(db, link))
    return result


def accept_invitation(db: Session, user: User, link_id: int):
    link = get_invitation_or_404(db, user, link_id)

    link.caregiver_id = user.id
    link.status = "accepted"

    saved = caregiver_repository.save_link(db, link)
    return make_patient_response(db, saved)


def reject_invitation(db: Session, user: User, link_id: int):
    link = get_invitation_or_404(db, user, link_id)

    link.status = "rejected"
    caregiver_repository.save_link(db, link)


# ---------------- Caregiver side ----------------


def list_my_patients(db: Session, user: User):
    links = caregiver_repository.get_patients_by_caregiver(db, user.id)

    result = []
    for link in links:
        result.append(make_patient_response(db, link))
    return result


def leave_patient(db: Session, user: User, link_id: int):
    link = caregiver_repository.get_link_by_id(db, link_id)

    if link is None or link.caregiver_id != user.id or link.status != "accepted":
        raise HTTPException(status_code=404, detail="Patient not found")

    caregiver_repository.delete_link(db, link)