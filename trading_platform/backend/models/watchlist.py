from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base
from backend.models.user import utcnow


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_watch_user_symbol"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String(20))
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
