from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    portfolio = relationship("Portfolio", back_populates="user", uselist=False, cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    watchlist = relationship("WatchlistItem", cascade="all, delete-orphan")
    orders = relationship("Order", cascade="all, delete-orphan")
    transactions = relationship("Transaction", cascade="all, delete-orphan")
    alerts = relationship("Alert", cascade="all, delete-orphan")


class UserSettings(Base):
    __tablename__ = "user_settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    theme: Mapped[str] = mapped_column(String(10), default="dark")
    chart_type: Mapped[str] = mapped_column(String(10), default="candles")
    timeframe: Mapped[str] = mapped_column(String(5), default="1h")
    default_symbol: Mapped[str] = mapped_column(String(20), default="BTC/USD")
    indicators: Mapped[str] = mapped_column(String(200), default="volume")
    user = relationship("User", back_populates="settings")
