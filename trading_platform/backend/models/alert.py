from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base
from backend.models.user import utcnow


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String(20))
    target_price: Mapped[float] = mapped_column(Float)
    condition: Mapped[str] = mapped_column(String(10))  # above | below
    status: Mapped[str] = mapped_column(String(10), default="active")  # active | triggered
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    triggered_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # alert | order | system
    message: Mapped[str] = mapped_column(String(300))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
