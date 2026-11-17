"""FastAPI application entry point.  Run:  uvicorn backend.main:app --reload"""
import asyncio
import contextlib
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend import database
from backend.config import settings
from backend.routers import alerts, auth, markets, portfolio, trading, users, watchlist
from backend.services import alert_service

log = logging.getLogger("chartly")


async def _worker():
    """Background task: fills limit orders & triggers alerts even when the user is offline."""
    while True:
        await asyncio.sleep(15)
        def job():
            with database.SessionLocal() as db:
                alert_service.run_all_users(db)
        try:
            await asyncio.to_thread(job)
        except Exception:  # never let the worker die
            log.exception("background worker error")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    task = asyncio.create_task(_worker()) if settings.BACKGROUND_WORKER else None
    yield
    if task:
        task.cancel()


app = FastAPI(
    title=settings.APP_NAME, version="1.0.0", lifespan=lifespan,
    description="REST API for the Chartly paper-trading platform (educational project – no real money).",
)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
                   allow_methods=["*"], allow_headers=["*"])
for r in (auth.router, users.router, markets.router, watchlist.router, trading.router, portfolio.router, alerts.router):
    app.include_router(r)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    msgs = [f"{'.'.join(str(p) for p in e['loc'][1:])}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": "; ".join(msgs)})


@app.get("/api/health", tags=["System"])
def health():
    return {"status": "ok"}
