from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.cron_security import verify_cron_secret
from app.database.connection import get_db
from app.schemas.job_schema import MissedDoseJobResponse
from app.schemas.response_schema import ApiResponse
from app.services import job_service

router = APIRouter(prefix="/internal/jobs", tags=["Internal Jobs"])


@router.post(
    "/missed-doses",
    response_model=ApiResponse[MissedDoseJobResponse],
    dependencies=[Depends(verify_cron_secret)],
)
def run_missed_dose_job(db: Session = Depends(get_db)):
    result = job_service.mark_missed_doses(db)
    return ApiResponse(message="Missed dose check completed", data=result)