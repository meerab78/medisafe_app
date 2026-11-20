from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import dose_repository
from app.schemas.job_schema import MissedDoseJobResponse

# One run handles at most this many doses, so the request finishes quickly
MAX_DOSES_PER_RUN = 500


def mark_missed_doses(db: Session):
    grace = timedelta(minutes=settings.missed_dose_grace_minutes)
    cutoff = datetime.now(timezone.utc) - grace

    doses = dose_repository.get_overdue_pending_doses(db, cutoff, MAX_DOSES_PER_RUN)

    for dose in doses:
        dose.status = "missed"

    dose_repository.commit(db)

    return MissedDoseJobResponse(missed_count=len(doses), checked_before=cutoff)