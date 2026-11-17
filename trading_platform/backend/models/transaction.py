from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base
from backend.models.user import utcnow


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(10))  # BUY | SELL
    symbol: Mapped[str] = mapped_column(String(20))
    quantity: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    total_value: Mapped[float] = mapped_column(Float)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
