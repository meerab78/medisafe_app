from datetime import datetime

from pydantic import BaseModel, EmailStr


class CaregiverInvite(BaseModel):
    email: EmailStr
    can_view_medications: bool = True
    can_view_health: bool = False
    receive_missed_alerts: bool = True


class CaregiverPermissionsUpdate(BaseModel):
    can_view_medications: bool
    can_view_health: bool
    receive_missed_alerts: bool


class CaregiverResponse(BaseModel):
    # What the PATIENT sees about a caregiver
    id: int
    email: str
    # None when that email has no account yet
    caregiver_name: str | None
    status: str
    can_view_medications: bool
    can_view_health: bool
    receive_missed_alerts: bool
    created_at: datetime


class PatientResponse(BaseModel):
    # What the CAREGIVER sees about a patient (id is the link id)
    id: int
    patient_id: int
    patient_name: str
    patient_email: str
    status: str
    can_view_medications: bool
    can_view_health: bool
    receive_missed_alerts: bool
    created_at: datetime


class InvitationResponse(BaseModel):
    # What the INVITED person sees before accepting
    id: int
    patient_name: str
    patient_email: str
    can_view_medications: bool
    can_view_health: bool
    receive_missed_alerts: bool
    created_at: datetime