from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, UserSettings
from backend.schemas.user import PasswordChange, SettingsOut, SettingsUpdate
from backend.security.authentication import get_current_user, hash_password, verify_password
from backend.services import market_data

router = APIRouter(prefix="/api/users", tags=["Users"])


def _settings(db: Session, user: User) -> UserSettings:
    s = db.scalar(select(UserSettings).where(UserSettings.user_id == user.id))
    if s is None:
        s = UserSettings(user_id=user.id)
        db.add(s)
        db.commit()
    return s


@router.get("/me/settings", response_model=SettingsOut)
def get_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _settings(db, user)


@router.put("/me/settings", response_model=SettingsOut)
def update_settings(data: SettingsUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = _settings(db, user)
    values = data.model_dump(exclude_none=True)
    if "default_symbol" in values:
        try:
            values["default_symbol"] = market_data.normalize_symbol(values["default_symbol"])
        except market_data.UnknownSymbol:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown default symbol")
    for k, v in values.items():
        setattr(s, k, v)
    db.commit()
    return s


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(data: PasswordChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    user.hashed_password = hash_password(data.new_password)
    db.commit()
