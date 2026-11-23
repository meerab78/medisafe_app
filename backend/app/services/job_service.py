import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import caregiver_repository, dose_repository
from app.schemas.job_schema import MissedDoseJobResponse
from app.services import notification_service

logger = logging.getLogger(__name__)

# One run handles at most this many doses, so the request finishes quickly
MAX_DOSES_PER_RUN = 500

# The alert text shows at most this many medicine names
MAX_NAMES_IN_ALERT = 3


def collect_missed_by_patient(db: Session, doses):
    # Returns a dictionary: patient id -> {"count": number of doses, "names": medicine names}
    missed_by_patient = {}

    for dose in doses:
        medication = dose_repository.get_medication_by_id_any(db, dose.medication_id)
        if medication is None:
            continue

        patient_id = medication.user_id
        if patient_id not in missed_by_patient:
            missed_by_patient[patient_id] = {"count": 0, "names": []}

        info = missed_by_patient[patient_id]
        info["count"] = info["count"] + 1
        if medication.name not in info["names"]:
            info["names"].append(medication.name)

    return missed_by_patient


def make_alert_body(patient_name: str, info):
    count = info["count"]
    if count == 1:
        dose_text = "1 dose"
    else:
        dose_text = str(count) + " doses"

    names = info["names"]
    shown_names = names[:MAX_NAMES_IN_ALERT]
    names_text = ", ".join(shown_names)
    if len(names) > MAX_NAMES_IN_ALERT:
        names_text = names_text + " and more"

    return patient_name + " missed " + dose_text + " (" + names_text + ")"


def send_missed_alerts(db: Session, missed_by_patient):
    alerts_sent = 0

    for patient_id in missed_by_patient:
        info = missed_by_patient[patient_id]

        patient = caregiver_repository.find_user_by_id(db, patient_id)
        if patient is None:
            continue

        caregiver_ids = caregiver_repository.get_alert_caregiver_ids(db, patient_id)
        if len(caregiver_ids) == 0:
            continue

        title = "Missed dose"
        body = make_alert_body(patient.full_name, info)
        data = {"type": "missed_dose", "patient_id": patient_id}

        # One push per caregiver for this patient, even if many doses were missed
        for caregiver_id in caregiver_ids:
            sent = notification_service.send_push_to_user(
                db, caregiver_id, title, body, data
            )
            alerts_sent = alerts_sent + sent

    return alerts_sent


def mark_missed_doses(db: Session):
    grace = timedelta(minutes=settings.missed_dose_grace_minutes)
    cutoff = datetime.now(timezone.utc) - grace

    doses = dose_repository.get_overdue_pending_doses(db, cutoff, MAX_DOSES_PER_RUN)

    # Collect the details first, then change the status
    missed_by_patient = collect_missed_by_patient(db, doses)

    for dose in doses:
        dose.status = "missed"

    dose_repository.commit(db)

    # The doses are saved now. A problem with the alerts must not break the job.
    alerts_sent = 0
    try:
        alerts_sent = send_missed_alerts(db, missed_by_patient)
    except Exception:
        logger.exception("Failed to send missed dose alerts")
        db.rollback()

    return MissedDoseJobResponse(
        missed_count=len(doses),
        checked_before=cutoff,
        alerts_sent=alerts_sent,
    )