from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Notification, User, UserSettings, WatchlistItem
from backend.schemas.user import LoginRequest, RegisterRequest, TokenResponse, UserOut
from backend.security.authentication import create_access_token, get_current_user, hash_password, verify_password
from backend.services import trading_engine

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
DEFAULT_WATCHLIST = ["BTC/USD", "ETH/USD", "SOL/USD", "AAPL", "TSLA", "NVDA", "EUR/USD", "XAU/USD"]


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(func.lower(User.username) == data.username.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
    if db.scalar(select(User).where(func.lower(User.email) == data.email.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(username=data.username, email=data.email.lower(), hashed_password=hash_password(data.password))
    db.add(user)
    db.flush()
    db.add(UserSettings(user_id=user.id))
    trading_engine.create_portfolio(db, user)
    for sym in DEFAULT_WATCHLIST:
        db.add(WatchlistItem(user_id=user.id, symbol=sym))
    db.add(Notification(user_id=user.id, kind="system",
                        message="Welcome! Your paper-trading account was funded with $100,000 of virtual money."))
    db.commit()
    return user


def _authenticate(db: Session, username: str, password: str) -> User:
    user = db.scalar(select(User).where(func.lower(User.username) == username.lower()))
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return TokenResponse(access_token=create_access_token(_authenticate(db, data.username, data.password).id))


@router.post("/token", response_model=TokenResponse, include_in_schema=True,
             summary="OAuth2 form login (used by the Swagger 'Authorize' button)")
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return TokenResponse(access_token=create_access_token(_authenticate(db, form.username, form.password).id))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
