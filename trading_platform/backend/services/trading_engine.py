"""Paper-trading engine. ALL trading maths and validation live here (backend only).

Educational simulation: no real money, no real brokerage.
Rules
  * Long-only (no short selling), no leverage, no fees.
  * Market orders fill immediately at the current quote.
  * Limit orders fill immediately if marketable (buy: price <= limit, sell: price >= limit)
    otherwise they stay `pending`; cash / shares are reserved for them.
  * Every state change happens in one DB transaction (commit or rollback).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import Notification, Order, Portfolio, PortfolioSnapshot, Position, Transaction, User
from backend.models.user import utcnow
from backend.services import market_data

EPS = 1e-9


class TradingError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message, self.status_code = message, status_code


def create_portfolio(db: Session, user: User) -> Portfolio:
    p = Portfolio(user_id=user.id, available_balance=settings.STARTING_BALANCE,
                  total_equity=settings.STARTING_BALANCE, initial_balance=settings.STARTING_BALANCE)
    db.add(p)
    return p


def get_portfolio(db: Session, user: User) -> Portfolio:
    p = db.scalar(select(Portfolio).where(Portfolio.user_id == user.id))
    if p is None:
        p = create_portfolio(db, user)
        db.flush()
    return p


def _reserved(db: Session, user_id: int) -> tuple[float, dict[str, float]]:
    """(cash reserved by pending buy limits, shares reserved by pending sell limits per symbol)."""
    cash, shares = 0.0, {}
    for o in db.scalars(select(Order).where(Order.user_id == user_id, Order.status == "pending")):
        if o.side == "buy":
            cash += o.quantity * (o.limit_price or 0)
        else:
            shares[o.symbol] = shares.get(o.symbol, 0.0) + o.quantity
    return cash, shares


def _get_position(db: Session, user_id: int, symbol: str) -> Position | None:
    return db.scalar(select(Position).where(Position.user_id == user_id, Position.symbol == symbol))


def _notify(db: Session, user_id: int, kind: str, msg: str):
    db.add(Notification(user_id=user_id, kind=kind, message=msg))


def _fill(db: Session, portfolio: Portfolio, order: Order, price: float) -> None:
    """Apply a fill to cash, position, transaction log. Caller commits."""
    qty = order.quantity
    total = round(qty * price, 8)
    realized = 0.0
    pos = _get_position(db, order.user_id, order.symbol)
    if order.side == "buy":
        if total > portfolio.available_balance + EPS:
            raise TradingError("Insufficient balance")
        portfolio.available_balance -= total
        if pos is None:
            db.add(Position(user_id=order.user_id, symbol=order.symbol, quantity=qty, average_entry_price=price))
        else:
            new_qty = pos.quantity + qty
            pos.average_entry_price = (pos.quantity * pos.average_entry_price + qty * price) / new_qty
            pos.quantity = new_qty
    else:
        if pos is None or pos.quantity + EPS < qty:
            raise TradingError("Insufficient position quantity")
        realized = round((price - pos.average_entry_price) * qty, 8)
        portfolio.available_balance += total
        portfolio.realized_pnl += realized
        pos.quantity -= qty
        if pos.quantity < 1e-8:
            db.delete(pos)
    order.status, order.execution_price, order.filled_at = "filled", price, utcnow()
    db.add(Transaction(user_id=order.user_id, order_id=order.id, transaction_type=order.side.upper(),
                       symbol=order.symbol, quantity=qty, price=price, total_value=total, realized_pnl=realized))
    _notify(db, order.user_id, "order",
            f"{order.side.upper()} {qty:g} {order.symbol} filled at {price:,.4f}")


def place_order(db: Session, user: User, symbol: str, side: str, quantity: float,
                order_type: str = "market", limit_price: float | None = None) -> Order:
    side, order_type = side.lower(), order_type.lower()
    if side not in ("buy", "sell"):
        raise TradingError("Side must be 'buy' or 'sell'")
    if order_type not in ("market", "limit"):
        raise TradingError("Order type must be 'market' or 'limit'")
    if quantity is None or quantity <= 0:
        raise TradingError("Quantity must be positive")
    if order_type == "limit" and (limit_price is None or limit_price <= 0):
        raise TradingError("Limit orders need a positive limit price")
    try:
        asset = market_data.get_asset(symbol)
    except market_data.UnknownSymbol:
        raise TradingError(f"Unknown asset symbol '{symbol}'", 404)

    try:
        portfolio = get_portfolio(db, user)
        process_pending(db, user, commit=False)
        quote = market_data.get_quote(asset.symbol)
        price = quote["price"]
        reserved_cash, reserved_shares = _reserved(db, user.id)
        free_cash = portfolio.available_balance - reserved_cash
        pos = _get_position(db, user.id, asset.symbol)
        held = (pos.quantity if pos else 0.0) - reserved_shares.get(asset.symbol, 0.0)

        marketable = order_type == "market" or (
            (side == "buy" and price <= limit_price) or (side == "sell" and price >= limit_price))
        ref_price = price if marketable else limit_price
        if side == "buy" and quantity * (limit_price if order_type == "limit" else price) > free_cash + EPS:
            raise TradingError(
                f"Insufficient balance: need {quantity * ref_price:,.2f}, available {free_cash:,.2f}")
        if side == "sell" and quantity > held + EPS:
            raise TradingError(f"Insufficient position: you can sell at most {max(held, 0):g} {asset.symbol}")

        order = Order(user_id=user.id, symbol=asset.symbol, order_type=order_type, side=side,
                      quantity=quantity, limit_price=limit_price if order_type == "limit" else None)
        db.add(order)
        db.flush()
        if marketable:
            _fill(db, portfolio, order, price)
        record_snapshot(db, user, portfolio, force=True)
        db.commit()
        return order
    except Exception:
        db.rollback()
        raise


def cancel_order(db: Session, user: User, order_id: int) -> Order:
    order = db.scalar(select(Order).where(Order.id == order_id, Order.user_id == user.id))
    if order is None:
        raise TradingError("Order not found", 404)
    if order.status != "pending":
        raise TradingError(f"Only pending orders can be cancelled (this one is {order.status})")
    order.status = "cancelled"
    db.commit()
    return order


def process_pending(db: Session, user: User, commit: bool = True) -> int:
    """Fill any pending limit orders whose price condition is now met."""
    pending = db.scalars(select(Order).where(Order.user_id == user.id, Order.status == "pending")
                         .order_by(Order.id)).all()
    if not pending:
        return 0
    portfolio = get_portfolio(db, user)
    filled = 0
    for o in pending:
        price = market_data.get_quote(o.symbol)["price"]
        if (o.side == "buy" and price <= o.limit_price) or (o.side == "sell" and price >= o.limit_price):
            try:
                _fill(db, portfolio, o, price)
                filled += 1
            except TradingError:
                o.status = "cancelled"
                _notify(db, user.id, "order", f"Order #{o.id} cancelled: insufficient funds/position")
    if commit:
        db.commit()
    return filled


def positions_view(db: Session, user: User) -> list[dict]:
    rows = []
    for p in db.scalars(select(Position).where(Position.user_id == user.id).order_by(Position.symbol)):
        q = market_data.get_quote(p.symbol)
        mv = p.quantity * q["price"]
        cost = p.quantity * p.average_entry_price
        rows.append({
            "symbol": p.symbol, "name": q["name"], "quantity": p.quantity,
            "average_entry_price": p.average_entry_price, "current_price": q["price"],
            "market_value": round(mv, 2), "cost_basis": round(cost, 2),
            "unrealized_pnl": round(mv - cost, 2),
            "unrealized_pnl_pct": round((mv / cost - 1) * 100, 3) if cost else 0.0,
            "daily_pnl": round(p.quantity * (q["price"] - q["prev_close"]), 2),
            "source": q["source"],
        })
    return rows


def portfolio_summary(db: Session, user: User) -> dict:
    process_pending(db, user)
    portfolio = get_portfolio(db, user)
    positions = positions_view(db, user)
    reserved_cash, _ = _reserved(db, user.id)
    pos_value = sum(p["market_value"] for p in positions)
    unrealized = sum(p["unrealized_pnl"] for p in positions)
    equity = portfolio.available_balance + pos_value
    portfolio.total_equity = equity
    record_snapshot(db, user, portfolio)
    db.commit()
    total_pnl = equity - portfolio.initial_balance
    return {
        "balance": round(portfolio.available_balance, 2),
        "available_balance": round(portfolio.available_balance - reserved_cash, 2),
        "reserved_balance": round(reserved_cash, 2),
        "positions_value": round(pos_value, 2),
        "total_equity": round(equity, 2),
        "initial_balance": portfolio.initial_balance,
        "realized_pnl": round(portfolio.realized_pnl, 2),
        "unrealized_pnl": round(unrealized, 2),
        "total_pnl": round(total_pnl, 2),
        "return_pct": round(total_pnl / portfolio.initial_balance * 100, 3),
        "daily_pnl": round(sum(p["daily_pnl"] for p in positions), 2),
        "positions": positions,
    }


def record_snapshot(db: Session, user: User, portfolio: Portfolio, force: bool = False) -> None:
    db.flush()  # sessions use autoflush=False: make pending position/cash changes visible first
    last = db.scalar(select(PortfolioSnapshot).where(PortfolioSnapshot.user_id == user.id)
                     .order_by(PortfolioSnapshot.id.desc()).limit(1))
    if not force and last and (utcnow() - last.created_at).total_seconds() < 60:
        return
    pos_value = sum(p["market_value"] for p in positions_view(db, user))
    db.add(PortfolioSnapshot(user_id=user.id, equity=portfolio.available_balance + pos_value))


def performance(db: Session, user: User) -> dict:
    summary = portfolio_summary(db, user)
    snaps = db.scalars(select(PortfolioSnapshot).where(PortfolioSnapshot.user_id == user.id)
                       .order_by(PortfolioSnapshot.id)).all()
    wins = db.scalar(select(func.count()).select_from(Transaction).where(
        Transaction.user_id == user.id, Transaction.transaction_type == "SELL", Transaction.realized_pnl > 0)) or 0
    sells = db.scalar(select(func.count()).select_from(Transaction).where(
        Transaction.user_id == user.id, Transaction.transaction_type == "SELL")) or 0
    return {
        "equity_curve": [{"time": s.created_at.isoformat(), "equity": round(s.equity, 2)} for s in snaps],
        "total_return_pct": summary["return_pct"], "realized_pnl": summary["realized_pnl"],
        "unrealized_pnl": summary["unrealized_pnl"], "closed_trades": sells,
        "win_rate_pct": round(wins / sells * 100, 1) if sells else None,
        "total_trades": db.scalar(select(func.count()).select_from(Transaction).where(Transaction.user_id == user.id)) or 0,
    }


def reset_account(db: Session, user: User) -> Portfolio:
    for model in (Position, Order, Transaction, PortfolioSnapshot):
        for row in db.scalars(select(model).where(model.user_id == user.id)):
            db.delete(row)
    p = get_portfolio(db, user)
    p.available_balance = p.total_equity = p.initial_balance = settings.STARTING_BALANCE
    p.realized_pnl = 0.0
    db.commit()
    return p
