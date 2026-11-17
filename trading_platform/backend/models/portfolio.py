from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base
from backend.models.user import utcnow


class Portfolio(Base):
    __tablename__ = "portfolios"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    available_balance: Mapped[float] = mapped_column(Float)  # cash
    total_equity: Mapped[float] = mapped_column(Float)
    initial_balance: Mapped[float] = mapped_column(Float)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    user = relationship("User", back_populates="portfolio")


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_position_user_symbol"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String(20))
    quantity: Mapped[float] = mapped_column(Float)
    average_entry_price: Mapped[float] = mapped_column(Float)


class PortfolioSnapshot(Base):
    """Periodic equity snapshot used for the performance (equity curve) chart."""
    __tablename__ = "portfolio_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    equity: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
