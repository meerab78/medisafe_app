from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user_model import User
from app.repositories import report_repository
from app.schemas.report_schema import (
    AdherenceReport,
    DayStats,
    HistoryDoseItem,
    HistoryResponse,
)

MAX_RANGE_DAYS = 92
PERIOD_DAYS = {"day": 1, "week": 7, "month": 30}


def get_user_today(user: User) -> date:
    try:
        zone = ZoneInfo(user.timezone)
    except (KeyError, ValueError):
        zone = timezone.utc
    return datetime.now(zone).date()


def check_date_range(start_date: date, end_date: date) -> None:
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must not be after end date",
        )
    day_count = (end_date - start_date).days + 1
    if day_count > MAX_RANGE_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot be more than 92 days",
        )


def get_history(
    db: Session,
    user: User,
    start_date: date | None,
    end_date: date | None,
    medication_id: int | None,
) -> HistoryResponse:
    if end_date is None:
        end_date = get_user_today(user)
    if start_date is None:
        start_date = end_date - timedelta(days=6)

    check_date_range(start_date, end_date)

    rows = report_repository.get_dose_rows_in_range(
        db, user.id, start_date, end_date, medication_id
    )

    items = []
    for dose_log, medication_name in rows:
        item = HistoryDoseItem(
            id=dose_log.id,
            medication_id=dose_log.medication_id,
            medication_name=medication_name,
            scheduled_date=dose_log.scheduled_date,
            scheduled_at=dose_log.scheduled_at,
            status=dose_log.status,
            taken_at=dose_log.taken_at,
        )
        items.append(item)

    return HistoryResponse(
        start_date=start_date,
        end_date=end_date,
        total=len(items),
        doses=items,
    )


def get_adherence_report(
    db: Session, user: User, period: str, end_date: date | None
) -> AdherenceReport:
    if end_date is None:
        end_date = get_user_today(user)

    day_count = PERIOD_DAYS[period]
    start_date = end_date - timedelta(days=day_count - 1)

    rows = report_repository.get_dose_rows_in_range(
        db, user.id, start_date, end_date
    )

    # Start with zero counts for every day in the period
    day_counts = {}
    for day_number in range(day_count):
        day = start_date + timedelta(days=day_number)
        day_counts[day] = {"taken": 0, "skipped": 0, "missed": 0, "pending": 0}

    # Count each dose on its day
    for dose_log, medication_name in rows:
        counts = day_counts[dose_log.scheduled_date]
        if dose_log.status in counts:
            counts[dose_log.status] = counts[dose_log.status] + 1

    days = []
    total_taken = 0
    total_skipped = 0
    total_missed = 0
    total_pending = 0

    for day_number in range(day_count):
        day = start_date + timedelta(days=day_number)
        counts = day_counts[day]
        day_total = (
            counts["taken"] + counts["skipped"] + counts["missed"] + counts["pending"]
        )
        day_stats = DayStats(
            day=day,
            taken=counts["taken"],
            skipped=counts["skipped"],
            missed=counts["missed"],
            pending=counts["pending"],
            total=day_total,
        )
        days.append(day_stats)

        total_taken = total_taken + counts["taken"]
        total_skipped = total_skipped + counts["skipped"]
        total_missed = total_missed + counts["missed"]
        total_pending = total_pending + counts["pending"]

    # Pending doses are not counted, because they are not decided yet
    decided = total_taken + total_skipped + total_missed
    adherence_percent = None
    if decided > 0:
        adherence_percent = round(total_taken * 100 / decided, 1)

    return AdherenceReport(
        period=period,
        start_date=start_date,
        end_date=end_date,
        taken=total_taken,
        skipped=total_skipped,
        missed=total_missed,
        pending=total_pending,
        total=decided + total_pending,
        adherence_percent=adherence_percent,
        days=days,
    )