from datetime import datetime

from pydantic import BaseModel, Field


class RefillCreate(BaseModel):
    quantity_added: int = Field(ge=1, le=10000)


class StockUpdate(BaseModel):
    stock_quantity: int = Field(ge=0, le=100000)


class StockResponse(BaseModel):
    medication_id: int
    medication_name: str
    stock_quantity: int
    low_stock_threshold: int
    is_low_stock: bool


class RefillResponse(StockResponse):
    quantity_added: int


class RefillLogItem(BaseModel):
    id: int
    quantity_added: int
    refilled_at: datetime


class RefillHistoryResponse(BaseModel):
    medication_id: int
    medication_name: str
    total: int
    refills: list[RefillLogItem]


class LowStockResponse(BaseModel):
    total: int
    medications: list[StockResponse]