from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.medication_model import Medication
from app.models.user_model import User
from app.repositories import refill_repository
from app.schemas.refill_schema import (
    LowStockResponse,
    RefillCreate,
    RefillHistoryResponse,
    RefillLogItem,
    RefillResponse,
    StockResponse,
    StockUpdate,
)


def is_low_stock(medication: Medication) -> bool:
    return medication.stock_quantity <= medication.low_stock_threshold


def make_stock_response(medication: Medication) -> StockResponse:
    return StockResponse(
        medication_id=medication.id,
        medication_name=medication.name,
        stock_quantity=medication.stock_quantity,
        low_stock_threshold=medication.low_stock_threshold,
        is_low_stock=is_low_stock(medication),
    )


def get_owned_medication_or_404(db: Session, user: User, medication_id: int):
    medication = refill_repository.get_user_medication(db, user.id, medication_id)
    if medication is None:
        raise HTTPException(status_code=404, detail="Medication not found")
    return medication


def get_active_medication(db: Session, user: User, medication_id: int):
    medication = get_owned_medication_or_404(db, user, medication_id)
    if not medication.is_active:
        raise HTTPException(status_code=400, detail="This medication is not active")
    return medication


def refill_medication(
    db: Session, user: User, medication_id: int, data: RefillCreate
) -> RefillResponse:
    medication = get_active_medication(db, user, medication_id)
    refill_repository.add_refill(db, medication, data.quantity_added)

    return RefillResponse(
        medication_id=medication.id,
        medication_name=medication.name,
        stock_quantity=medication.stock_quantity,
        low_stock_threshold=medication.low_stock_threshold,
        is_low_stock=is_low_stock(medication),
        quantity_added=data.quantity_added,
    )


def update_stock(
    db: Session, user: User, medication_id: int, data: StockUpdate
) -> StockResponse:
    medication = get_active_medication(db, user, medication_id)
    refill_repository.set_stock(db, medication, data.stock_quantity)
    return make_stock_response(medication)


def get_refill_history(
    db: Session, user: User, medication_id: int
) -> RefillHistoryResponse:
    medication = get_owned_medication_or_404(db, user, medication_id)
    logs = refill_repository.get_refills_for_medication(db, medication.id)

    items = []
    for log in logs:
        item = RefillLogItem(
            id=log.id,
            quantity_added=log.quantity_added,
            refilled_at=log.refilled_at,
        )
        items.append(item)

    return RefillHistoryResponse(
        medication_id=medication.id,
        medication_name=medication.name,
        total=len(items),
        refills=items,
    )


def get_low_stock(db: Session, user: User) -> LowStockResponse:
    medications = refill_repository.get_low_stock_medications(db, user.id)

    items = []
    for medication in medications:
        items.append(make_stock_response(medication))

    return LowStockResponse(total=len(items), medications=items)