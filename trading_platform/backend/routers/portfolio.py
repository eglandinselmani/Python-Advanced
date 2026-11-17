from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas.trading import PortfolioOut
from backend.security.authentication import get_current_user
from backend.services import trading_engine

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


@router.get("", response_model=PortfolioOut)
def portfolio(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return trading_engine.portfolio_summary(db, user)


@router.get("/balance")
def balance(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = trading_engine.portfolio_summary(db, user)
    return {k: s[k] for k in ("balance", "available_balance", "reserved_balance", "positions_value", "total_equity")}


@router.get("/performance")
def performance(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return trading_engine.performance(db, user)


@router.post("/reset", response_model=PortfolioOut, summary="Reset the paper account to $100,000")
def reset(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trading_engine.reset_account(db, user)
    return trading_engine.portfolio_summary(db, user)
