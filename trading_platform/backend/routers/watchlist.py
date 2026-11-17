from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, WatchlistItem
from backend.schemas.trading import WatchlistAdd, WatchlistItemOut
from backend.schemas.market import Quote
from backend.security.authentication import get_current_user
from backend.services import market_data

router = APIRouter(prefix="/api/watchlist", tags=["Watchlist"])


def _items(db, user):
    return db.scalars(select(WatchlistItem).where(WatchlistItem.user_id == user.id)
                      .order_by(WatchlistItem.id)).all()


@router.get("", response_model=list[dict], summary="Watchlist with live quotes")
def get_watchlist(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = _items(db, user)
    quotes = {q["symbol"]: q for q in market_data.get_quotes([i.symbol for i in items])} if items else {}
    return [{**quotes[i.symbol], "favorite": i.favorite} for i in items if i.symbol in quotes]


@router.post("", response_model=WatchlistItemOut, status_code=status.HTTP_201_CREATED)
def add(data: WatchlistAdd, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        sym = market_data.normalize_symbol(data.symbol)
    except market_data.UnknownSymbol:
        raise HTTPException(404, f"Unknown asset '{data.symbol}'")
    if any(i.symbol == sym for i in _items(db, user)):
        raise HTTPException(409, f"{sym} is already in your watchlist")
    item = WatchlistItem(user_id=user.id, symbol=sym)
    db.add(item)
    db.commit()
    return WatchlistItemOut(symbol=sym, favorite=False, added_at=item.created_at)


@router.delete("/{symbol:path}", status_code=status.HTTP_204_NO_CONTENT)
def remove(symbol: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        sym = market_data.normalize_symbol(symbol)
    except market_data.UnknownSymbol:
        raise HTTPException(404, f"Unknown asset '{symbol}'")
    item = next((i for i in _items(db, user) if i.symbol == sym), None)
    if item is None:
        raise HTTPException(404, f"{sym} is not in your watchlist")
    db.delete(item)
    db.commit()


@router.put("/{symbol:path}/favorite", response_model=WatchlistItemOut, summary="Toggle favourite flag")
def toggle_favorite(symbol: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        sym = market_data.normalize_symbol(symbol)
    except market_data.UnknownSymbol:
        raise HTTPException(404, f"Unknown asset '{symbol}'")
    item = next((i for i in _items(db, user) if i.symbol == sym), None)
    if item is None:
        raise HTTPException(404, f"{sym} is not in your watchlist")
    item.favorite = not item.favorite
    db.commit()
    return WatchlistItemOut(symbol=sym, favorite=item.favorite, added_at=item.created_at)
