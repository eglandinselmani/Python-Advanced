# Database design (SQLite via SQLAlchemy)

## Entity-relationship diagram
```
            ┌───────────┐ 1      1 ┌────────────────┐
            │   users   │──────────│ user_settings  │
            │ id PK     │          └────────────────┘
            │ username U│ 1      1 ┌────────────────┐
            │ email U   │──────────│  portfolios    │  (cash, equity, initial, realized_pnl)
            │ hashed_pw │ 1      N ┌────────────────┐
            │ created_at│──────────│  positions     │  UNIQUE(user_id, symbol)
            └─────┬─────┘ 1      N ├────────────────┤
                  │───────────────│  orders        │──┐ 1
                  │ 1      N      ├────────────────┤  │ N
                  │───────────────│  transactions  │◀─┘ (order_id, nullable)
                  │ 1      N      ├────────────────┤
                  │───────────────│ watchlist_items│  UNIQUE(user_id, symbol)
                  │ 1      N      ├────────────────┤
                  │───────────────│  alerts        │
                  │ 1      N      ├────────────────┤
                  │───────────────│ notifications  │
                  │ 1      N      ├────────────────┤
                  └───────────────│ portfolio_snapshots│ (equity curve)
```
All child tables reference `users.id` with `ON DELETE CASCADE`; SQLite foreign keys are enabled (`PRAGMA foreign_keys=ON`).

| Table | Columns |
|---|---|
| users | id, username (unique), email (unique), hashed_password, created_at |
| user_settings | id, user_id (unique), theme, chart_type, timeframe, default_symbol, indicators |
| portfolios | id, user_id (unique), available_balance (cash), total_equity, initial_balance, realized_pnl |
| positions | id, user_id, symbol, quantity, average_entry_price |
| orders | id, user_id, symbol, order_type (market/limit), side (buy/sell), quantity, limit_price, execution_price, status (pending/filled/cancelled), created_at, filled_at |
| transactions | id, user_id, order_id, transaction_type (BUY/SELL), symbol, quantity, price, total_value, realized_pnl, created_at |
| watchlist_items | id, user_id, symbol, favorite, created_at |
| alerts | id, user_id, symbol, target_price, condition (above/below), status (active/triggered), created_at, triggered_at, triggered_price |
| notifications | id, user_id, kind, message, is_read, created_at |
| portfolio_snapshots | id, user_id, equity, created_at |

Inspect the DB: `sqlite3 data/trading.db ".tables"` or any SQLite browser. Persistence across restarts is covered by
`tests/test_database.py::test_full_integration_flow_with_restart`.
