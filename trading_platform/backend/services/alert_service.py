"""Price-alert evaluation and the notification feed."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import Alert, Notification, User
from backend.models.user import utcnow
from backend.services import market_data, trading_engine


def check_alerts(db: Session, user: User) -> list[Alert]:
    triggered = []
    for a in db.scalars(select(Alert).where(Alert.user_id == user.id, Alert.status == "active")):
        price = market_data.get_quote(a.symbol)["price"]
        if (a.condition == "above" and price >= a.target_price) or (a.condition == "below" and price <= a.target_price):
            a.status, a.triggered_at, a.triggered_price = "triggered", utcnow(), price
            db.add(Notification(user_id=user.id, kind="alert",
                                message=f"Alert: {a.symbol} is {a.condition} {a.target_price:,.4f} (now {price:,.4f})"))
            triggered.append(a)
    db.commit()
    return triggered


def run_all_users(db: Session) -> None:
    """Called by the background worker: fill limit orders + trigger alerts for every user."""
    for user in db.scalars(select(User)):
        try:
            trading_engine.process_pending(db, user)
            check_alerts(db, user)
        except Exception:
            db.rollback()
