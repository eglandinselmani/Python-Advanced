from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base
from backend.models.user import utcnow


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String(20))
    order_type: Mapped[str] = mapped_column(String(10))   # market | limit
    side: Mapped[str] = mapped_column(String(4))           # buy | sell
    quantity: Mapped[float] = mapped_column(Float)
    limit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    execution_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="pending")  # pending|filled|cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    filled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
