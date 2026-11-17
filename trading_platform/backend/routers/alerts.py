from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Alert, Notification, User
from backend.schemas.trading import AlertCreate, AlertOut, NotificationOut
from backend.security.authentication import get_current_user
from backend.services import alert_service, market_data

router = APIRouter(prefix="/api/alerts", tags=["Alerts & notifications"])


@router.get("", response_model=list[AlertOut])
def list_alerts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    alert_service.check_alerts(db, user)
    return db.scalars(select(Alert).where(Alert.user_id == user.id).order_by(Alert.id.desc())).all()


@router.post("", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
def create_alert(data: AlertCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        sym = market_data.normalize_symbol(data.symbol)
    except market_data.UnknownSymbol:
        raise HTTPException(404, f"Unknown asset '{data.symbol}'")
    alert = Alert(user_id=user.id, symbol=sym, target_price=data.target_price, condition=data.condition)
    db.add(alert)
    db.commit()
    return alert


@router.get("/notifications", response_model=list[NotificationOut])
def notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    alert_service.check_alerts(db, user)
    return db.scalars(select(Notification).where(Notification.user_id == user.id)
                      .order_by(Notification.id.desc()).limit(50)).all()


@router.post("/notifications/read", status_code=status.HTTP_204_NO_CONTENT, summary="Mark all as read")
def mark_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for n in db.scalars(select(Notification).where(Notification.user_id == user.id, Notification.is_read.is_(False))):
        n.is_read = True
    db.commit()


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(alert_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    alert = db.scalar(select(Alert).where(Alert.id == alert_id, Alert.user_id == user.id))
    if alert is None:
        raise HTTPException(404, "Alert not found")
    db.delete(alert)
    db.commit()
