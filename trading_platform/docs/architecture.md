# Architecture

```
┌────────────────────┐   HTTP + JSON (Bearer JWT)   ┌──────────────────────────────┐   SQLAlchemy   ┌──────────┐
│  Streamlit frontend│ ───────────────────────────▶ │       FastAPI backend         │ ─────────────▶ │  SQLite  │
│  (port 8501)       │ ◀─────────────────────────── │       (port 8000, /docs)      │ ◀───────────── │ trading.db│
│  pages/components  │                              │ routers → services → models   │                └──────────┘
│  api_client.py     │                              │        ▲            ▲          │
└────────────────────┘                              │  market_data   trading_engine  │──▶ Yahoo Finance / RSS (optional)
                                                    │  technical_analysis, alerts    │    (fallback: labelled simulator)
                                                    └──────────────────────────────┘
```

## Frontend (Streamlit, `frontend/`)
* `app.py` – page config, authentication gate, theme injection, left toolbar, top bar, page router (`st.session_state.page`).
* `api_client.py` – the **only** place that speaks HTTP; converts errors into `APIError` / `BackendUnavailable`.
* `state.py` – session helpers (`api()`, `call()` for friendly error handling, settings cache).
* `components/` – `charts.py` (Plotly engine), `watchlist_panel.py` (auto-refreshing `st.fragment`), `trading_panel.py` (order
  ticket), `market_cards.py`, `sidebar.py` (toolbar + top bar), `styles.py` (custom CSS, light/dark).
* `pages/` – dashboard, markets (+heatmap), watchlist, asset_details, paper_trading, portfolio, alerts, news, settings.
  Each exposes `render()`. The frontend contains **no trading maths and no database access**.

## Backend (FastAPI, `backend/`)
* `routers/` – thin HTTP layer: auth, users, markets, watchlist, trading, portfolio, alerts.
* `schemas/` – Pydantic request/response models (validation: positive quantities, valid order types, password rules, e-mail…).
* `services/` – business logic: `market_data` (live provider + simulator), `technical_analysis`, `trading_engine`,
  `alert_service`, `news`.
* `models/` – SQLAlchemy ORM tables. `security/authentication.py` – bcrypt hashing + JWT + `get_current_user` dependency.
* `main.py` – app factory, CORS, validation error handler, optional background worker (every 15 s fills limit orders and
  triggers alerts for all users, even offline).

## Request flow example – "Buy 10 AAPL"
1. User clicks **Buy** → `trading_panel.py` calls `APIClient.order("buy", "AAPL", 10)`.
2. `POST /api/trading/buy` with `Authorization: Bearer <JWT>` → `get_current_user` validates the token.
3. Pydantic validates the body (`quantity > 0`, `order_type ∈ {market, limit}`).
4. `trading_engine.place_order` loads quote, checks free cash, creates the `Order`, applies the fill to `Portfolio`,
   `Position`, `Transaction`, records an equity snapshot and **commits once** (rollback on any error).
5. JSON response → UI shows a toast, next run re-reads portfolio from the API.

## Security
bcrypt hashes (never plain text), JWT (HS256, expiry), secret from env/`.env` or auto-generated into `data/.secret_key`,
every private query filtered by `user_id` (users cannot read each other's data – tested), ORM parameterised queries
(no SQL injection), strict input validation, generic login error (no user enumeration).
