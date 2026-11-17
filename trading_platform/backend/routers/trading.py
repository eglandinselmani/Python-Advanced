from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Order, Transaction, User
from backend.schemas.trading import OrderOut, OrderRequest, PositionOut, TransactionOut
from backend.security.authentication import get_current_user
from backend.services import trading_engine
from backend.services.trading_engine import TradingError

router = APIRouter(prefix="/api/trading", tags=["Paper trading"])


def _run(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except TradingError as e:
        raise HTTPException(e.status_code, e.message)


@router.post("/buy", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def buy(req: OrderRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _run(trading_engine.place_order, db, user, req.symbol, "buy", req.quantity, req.order_type, req.limit_price)


@router.post("/sell", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def sell(req: OrderRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _run(trading_engine.place_order, db, user, req.symbol, "sell", req.quantity, req.order_type, req.limit_price)


@router.get("/orders", response_model=list[OrderOut])
def orders(status_filter: str | None = Query(None, alias="status", pattern="^(pending|filled|cancelled)$"),
           limit: int = Query(100, ge=1, le=500),
           user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trading_engine.process_pending(db, user)
    q = select(Order).where(Order.user_id == user.id)
    if status_filter:
        q = q.where(Order.status == status_filter)
    return db.scalars(q.order_by(Order.id.desc()).limit(limit)).all()


@router.delete("/orders/{order_id}", response_model=OrderOut, summary="Cancel a pending limit order")
def cancel(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _run(trading_engine.cancel_order, db, user, order_id)


@router.get("/positions", response_model=list[PositionOut])
def positions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trading_engine.process_pending(db, user)
    return trading_engine.positions_view(db, user)


@router.get("/history", response_model=list[TransactionOut], summary="Transaction history")
def history(limit: int = Query(200, ge=1, le=1000), user: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    return db.scalars(select(Transaction).where(Transaction.user_id == user.id)
                      .order_by(Transaction.id.desc()).limit(limit)).all()
