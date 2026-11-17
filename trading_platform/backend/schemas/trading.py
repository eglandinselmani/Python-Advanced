from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrderRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    quantity: float = Field(gt=0, le=1e12)
    order_type: Literal["market", "limit"] = "market"
    limit_price: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _limit(self):
        if self.order_type == "limit" and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        return self


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    symbol: str
    order_type: str
    side: str
    quantity: float
    limit_price: float | None
    execution_price: float | None
    status: str
    created_at: datetime
    filled_at: datetime | None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    transaction_type: str
    symbol: str
    quantity: float
    price: float
    total_value: float
    realized_pnl: float
    created_at: datetime


class PositionOut(BaseModel):
    symbol: str
    name: str
    quantity: float
    average_entry_price: float
    current_price: float
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    daily_pnl: float
    source: str


class PortfolioOut(BaseModel):
    balance: float
    available_balance: float
    reserved_balance: float
    positions_value: float
    total_equity: float
    initial_balance: float
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    return_pct: float
    daily_pnl: float
    positions: list[PositionOut]


class WatchlistAdd(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)


class WatchlistItemOut(BaseModel):
    symbol: str
    favorite: bool
    added_at: datetime


class AlertCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    target_price: float = Field(gt=0)
    condition: Literal["above", "below"]


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    symbol: str
    target_price: float
    condition: str
    status: str
    created_at: datetime
    triggered_at: datetime | None
    triggered_price: float | None


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    message: str
    is_read: bool
    created_at: datetime
