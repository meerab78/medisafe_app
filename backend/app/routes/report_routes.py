from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.report_schema import AdherenceReport, HistoryResponse
from app.schemas.response_schema import ApiResponse
from app.services import report_service

router = APIRouter(tags=["Reports"])


@router.get("/history", response_model=ApiResponse[HistoryResponse])
def get_dose_history(
    start_date: date | None = None,
    end_date: date | None = None,
    medication_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    history = report_service.get_history(
        db, current_user, start_date, end_date, medication_id
    )
    return ApiResponse(message="History fetched successfully", data=history)


@router.get("/reports/adherence", response_model=ApiResponse[AdherenceReport])
def get_adherence_report(
    period: Literal["day", "week", "month"] = "week",
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = report_service.get_adherence_report(db, current_user, period, end_date)
    return ApiResponse(message="Report fetched successfully", data=report)