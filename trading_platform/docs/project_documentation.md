# Chartly – Final School Project Documentation

*A TradingView-inspired paper-trading platform written entirely in Python (Streamlit + FastAPI + SQLAlchemy).*

## 1. Project introduction
Chartly is a web-based financial terminal. Users register, watch markets on professional interactive charts, add technical
indicators, and practise trading with **virtual money** ($100,000). It is structured like a real fintech product:
a browser UI, a separate REST API, a database and authentication. The look is inspired by TradingView (dark theme, left
toolbar, central chart, right watchlist) but uses original branding and assets.

## 2. Problem statement
Beginners want to learn trading and chart analysis but risking real money is dangerous, and professional platforms are
complex. There is a need for a safe, educational environment where one can analyse charts and test strategies without risk.

## 3. Project objectives
1. Build a genuine client–server application in Python only.
2. Provide interactive candlestick/line/area charts with indicators and 9 timeframes.
3. Implement an accurate paper-trading engine with portfolio, P&L and history.
4. Persist all user data (accounts, watchlists, trades, alerts, settings) in SQLite.
5. Secure the system with bcrypt password hashing and JWT-protected endpoints.
6. Test the system automatically and document it.

## 4. Functional requirements
FR1 register/login/logout · FR2 view quotes for 35 assets in 5 classes · FR3 charts (candles/line/area/volume, zoom, pan,
crosshair, timeframes 1m–1M) · FR4 indicators (SMA, EMA, Bollinger, RSI, MACD, volume) · FR5 watchlist add/remove/search/favourite
· FR6 market overview (gainers, losers, most active, stats, heatmap) · FR7 asset details (price, change, volume, market cap, high/low,
performance, description) · FR8 market & limit buy/sell orders · FR9 positions, portfolio, realized/unrealized P&L ·
FR10 order and transaction history · FR11 price alerts + notifications · FR12 news + economic calendar · FR13 user settings
(theme, chart type, timeframe, default symbol/indicators) and password change · FR14 account reset.

## 5. Non-functional requirements
Security (hashing, JWT, per-user data isolation, validation) · Reliability (DB transactions, rollback, backend-down message) ·
Usability (professional dark/light UI, responsive layout) · Performance (quote caching, vectorised NumPy simulation,
auto-refreshing watchlist) · Maintainability (layered architecture, 69 automated tests) · Honesty (simulated data is always labelled).

## 6. Technologies used
Python 3.12+ · Streamlit (UI) · Plotly (charts) · Pandas/NumPy (data & indicators) · FastAPI + Uvicorn (REST API) · Pydantic
(validation) · SQLAlchemy 2 + SQLite (database) · bcrypt + PyJWT (security) · requests (HTTP client) · pytest + FastAPI
TestClient + Streamlit AppTest (testing). No JavaScript/React/Node code was written.

## 7. Frontend architecture
See `architecture.md`. Streamlit pages call `api_client.py`; custom CSS (`components/styles.py`) creates the TradingView look.
The frontend shows data and sends user actions; it never accesses the DB and contains no trading maths.

## 8. Backend architecture
Routers (HTTP) → Services (business logic) → Models (ORM). Pydantic schemas validate input/output. A background task
fills limit orders and triggers alerts even when nobody is logged in.

## 9. Client-server communication
The browser talks to Streamlit; Streamlit (Python) calls the FastAPI backend with `requests`, sending JSON and the header
`Authorization: Bearer <JWT>`. Errors are returned with proper HTTP codes and a `detail` message that the UI displays.

## 10. REST API
Interactive documentation: **http://localhost:8000/docs** (use *Authorize* with a username/password).

| Group | Endpoints |
|---|---|
| Auth | `POST /api/auth/register` (201/409/422) · `POST /api/auth/login` · `POST /api/auth/token` (Swagger form) · `GET /api/auth/me` |
| Users | `GET/PUT /api/users/me/settings` · `POST /api/users/me/password` |
| Markets | `GET /api/markets` · `/status` · `/overview` · `/news` · `/calendar` · `/{symbol}` · `/{symbol}/history?timeframe=&limit=` · `/{symbol}/indicators?indicators=sma:20,rsi:14,macd,bb:20,vol` |
| Watchlist | `GET/POST /api/watchlist` · `DELETE /api/watchlist/{symbol}` · `PUT /api/watchlist/{symbol}/favorite` |
| Trading | `POST /api/trading/buy` · `/sell` · `GET /orders` · `DELETE /orders/{id}` · `GET /positions` · `GET /history` |
| Portfolio | `GET /api/portfolio` · `/balance` · `/performance` · `POST /reset` |
| Alerts | `GET/POST /api/alerts` · `DELETE /api/alerts/{id}` · `GET /api/alerts/notifications` · `POST /notifications/read` |

Symbols in URLs accept `BTC-USD`, `BTC/USD` or `btcusd`. Status codes: 200/201/204 success, 400 business rule broken (e.g.
insufficient balance), 401 not authenticated, 404 unknown asset/record, 409 duplicate, 422 invalid input.

## 11. Database structure and 12. relationships
See `database_design.md` (10 tables; one user has one portfolio, one settings row and many positions, orders, transactions,
watchlist items, alerts, notifications and snapshots; each transaction optionally references the order that created it).

## 13. Authentication and security
* Passwords are hashed with **bcrypt** (salted); plain passwords are never stored or returned.
* Login returns a **JWT** (HS256, 12 h) containing the user id; protected routes use the `get_current_user` dependency.
* Password policy: 8–72 characters, at least one letter and one digit. Usernames: 3–30 safe characters. E-mail validated.
* Data isolation: every query filters on the authenticated user's id – tested (`test_users_cannot_see_each_other`).
* The secret key comes from the environment (`SECRET_KEY`) or is generated once into `data/.secret_key`.

## 14. Trading simulator explanation
All maths runs in `backend/services/trading_engine.py` inside one DB transaction.
* **Market order** – executes immediately at the current quote.
* **Limit order** – buy fills when price ≤ limit, sell when price ≥ limit. If already satisfied it fills at once at the market
  price; otherwise it is *pending*; cash (buy) or shares (sell) are **reserved**, so you cannot spend or sell them twice.
  Pending orders are matched on every request and by the 15-second background worker; they can be cancelled.
* **Buy**: `cash −= qty × price`; position average entry = `(old_qty × old_avg + qty × price) / (old_qty + qty)`.
* **Sell**: `realized P&L = (price − avg_entry) × qty`; `cash += qty × price`; position shrinks/closes.
* **Unrealized P&L** = `qty × (last price − avg entry)`; **Equity** = cash + Σ market value;
  **Total P&L** = equity − $100,000 = realized + unrealized.
* **Daily P&L** = Σ `qty × (price − previous close)`.
* Validation: symbol exists, quantity > 0, order type/side valid, enough free cash, enough unreserved shares. No short
  selling, leverage or fees. Failed orders leave no trace (rollback).

## 15. Technical indicators explanation
| Indicator | Formula (implemented in `technical_analysis.py`) |
|---|---|
| SMA(n) | average of last n closes |
| EMA(n) | `EMA_t = α·close_t + (1−α)·EMA_{t−1}`, `α = 2/(n+1)` |
| RSI(14) | Wilder: first averages = simple mean of 14 gains/losses, then `avg = (prev·13 + current)/14`; `RSI = 100 − 100/(1+avgGain/avgLoss)` |
| MACD | `EMA12 − EMA26`; signal = EMA9 of MACD; histogram = MACD − signal |
| Bollinger | SMA20 ± 2 × standard deviation |
| Volume | volume bars (green/red), volume SMA, On-Balance Volume |
Verified against hand-computed values and a published RSI example (70.53), and cross-checked with an independent loop implementation.

## 16. Testing documentation
`pytest -q` → **69 tests, all passing**.
| File | What it proves |
|---|---|
| `test_auth.py` | registration, duplicate handling, validation, bcrypt hashing, login errors, protected routes (401), per-user isolation, settings, password change |
| `test_markets.py` | quotes, filters, symbol formats, all 9 timeframes (OHLC validity), overview, news/calendar labelled as sample, every indicator vs hand calculations, indicator API errors |
| `test_trading.py` | exact cash/position/avg-price/realized-P&L maths, equity identity, rejections (balance, quantity, symbol, order type), limit orders (pending, reservation, fill, cancel), alerts, reset, equity-curve regression |
| `test_database.py` | tables, default 8-asset watchlist, add/remove/favourite, per-user watchlists, **full integration flow with a simulated restart** (register → login → watchlist → buy → portfolio → sell → history → restart → data and old JWT still valid) |
| `test_frontend.py` | the real Streamlit app run with AppTest against the real API: login/register through the UI, wrong password error, all 9 pages render without exceptions, navigation, buying/selling through the order ticket, settings saved, watchlist add/remove, alert creation, friendly "backend down" message |

Bugs found and fixed by testing/inspection: RSI used the wrong seeding (now canonical Wilder); "Top losers" listed rising assets;
equity snapshots omitted just-opened positions (autoflush); light-theme widgets stayed dark; sidebar CSS leaked into the layout.
Manual visual checks were done in headless Chromium on every page in dark and light themes.

## 17. Installation instructions
See `README.md` (`pip install -r requirements.txt` then `python run.py`).

## 18. Screenshots
`docs/screenshots/`: `01_login`, `02_dashboard`, `03_markets`, `04_heatmap`, `05_asset_details`, `06_paper_trading`,
`07_portfolio`, `08_alerts`, `09_watchlist`, `10_news`. (Taken with simulated data, hence the SIMULATED badges.)

## 19. Future improvements
Persistent login across refresh (cookies), Alembic migrations, WebSocket streaming prices, stop-loss/take-profit orders,
short selling & fees, more indicators and drawing persistence, real economic-calendar API, e-mail/push alerts,
PostgreSQL + Docker deployment, social features/leaderboards.

## 20. Final conclusion
The project meets its goals: a Python-only, genuinely separated frontend and backend, a TradingView-style interface,
interactive charts with indicators, an accurate and validated paper-trading engine, persistent user accounts and a
documented, tested REST API. It demonstrates layered architecture, secure authentication, transaction-safe database use and
honest data labelling. It is an educational tool – not financial advice.

## Demo script for the presentation
1. `python run.py`; open `:8000/docs`, register via Swagger, *Authorize*, call `GET /api/markets/BTC-USD/indicators`.
2. Open `:8501`, create an account, show the dashboard: switch timeframe/chart type, add RSI + MACD + Bollinger.
3. Add a symbol to the watchlist; open Asset Details; create an alert.
4. Buy 0.1 BTC (market) and a limit order below the price; open Portfolio → show P&L, allocation, equity curve.
5. Sell part of the position; show realized P&L and transaction history.
6. Stop and restart `python run.py` → log in again: everything is still there (show `data/trading.db` with sqlite3).
