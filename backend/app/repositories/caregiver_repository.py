from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.caregiver_link_model import CaregiverLink
from app.models.user_model import User


def find_user_by_email(db: Session, email: str):
    query = select(User).where(User.email == email)
    return db.scalar(query)


def find_user_by_id(db: Session, user_id: int):
    return db.get(User, user_id)


def get_link_by_id(db: Session, link_id: int):
    return db.get(CaregiverLink, link_id)


def get_link_by_patient_and_email(db: Session, patient_id: int, email: str):
    query = select(CaregiverLink).where(
        CaregiverLink.patient_id == patient_id,
        CaregiverLink.invited_email == email,
    )
    return db.scalar(query)


def get_active_links_by_patient(db: Session, patient_id: int):
    # Pending and accepted links (rejected ones are hidden)
    query = select(CaregiverLink).where(CaregiverLink.patient_id == patient_id)
    query = query.where(CaregiverLink.status.in_(["pending", "accepted"]))
    query = query.order_by(CaregiverLink.id)
    return list(db.scalars(query).all())


def get_pending_invitations_by_email(db: Session, email: str):
    query = select(CaregiverLink).where(
        CaregiverLink.invited_email == email,
        CaregiverLink.status == "pending",
    )
    query = query.order_by(CaregiverLink.id)
    return list(db.scalars(query).all())


def get_patients_by_caregiver(db: Session, caregiver_id: int):
    query = select(CaregiverLink).where(
        CaregiverLink.caregiver_id == caregiver_id,
        CaregiverLink.status == "accepted",
    )
    query = query.order_by(CaregiverLink.id)
    return list(db.scalars(query).all())


def save_link(db: Session, link: CaregiverLink):
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def delete_link(db: Session, link: CaregiverLink):
    db.delete(link)
    db.commit()

def get_accepted_link(db: Session, caregiver_id: int, patient_id: int):
    # The link must belong to this caregiver, this patient, and be accepted
    query = select(CaregiverLink).where(
        CaregiverLink.caregiver_id == caregiver_id,
        CaregiverLink.patient_id == patient_id,
        CaregiverLink.status == "accepted",
    )
    return db.scalar(query)


def get_alert_caregiver_ids(db: Session, patient_id: int):
    # Accepted caregivers who want missed-dose alerts
    query = select(CaregiverLink).where(
        CaregiverLink.patient_id == patient_id,
        CaregiverLink.status == "accepted",
        CaregiverLink.receive_missed_alerts.is_(True),
    )
    links = list(db.scalars(query).all())

    caregiver_ids = []
    for link in links:
        if link.caregiver_id is not None:
            caregiver_ids.append(link.caregiver_id)
    return caregiver_ids