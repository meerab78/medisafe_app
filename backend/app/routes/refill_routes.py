from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.refill_schema import (
    LowStockResponse,
    RefillCreate,
    RefillHistoryResponse,
    RefillResponse,
    StockResponse,
    StockUpdate,
)
from app.schemas.response_schema import ApiResponse
from app.services import refill_service

router = APIRouter(tags=["Refills"])


@router.post(
    "/medications/{medication_id}/refill",
    response_model=ApiResponse[RefillResponse],
    status_code=status.HTTP_201_CREATED,
)
def refill_medication(
    medication_id: int,
    data: RefillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = refill_service.refill_medication(db, current_user, medication_id, data)
    return ApiResponse(message="Stock refilled successfully", data=result)


@router.put(
    "/medications/{medication_id}/stock",
    response_model=ApiResponse[StockResponse],
)
def update_stock(
    medication_id: int,
    data: StockUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = refill_service.update_stock(db, current_user, medication_id, data)
    return ApiResponse(message="Stock updated successfully", data=result)


@router.get(
    "/medications/{medication_id}/refills",
    response_model=ApiResponse[RefillHistoryResponse],
)
def get_refill_history(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = refill_service.get_refill_history(db, current_user, medication_id)
    return ApiResponse(message="Refill history fetched successfully", data=result)


@router.get("/refills/low-stock", response_model=ApiResponse[LowStockResponse])
def get_low_stock(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = refill_service.get_low_stock(db, current_user)
    return ApiResponse(message="Low stock medications fetched successfully", data=result)