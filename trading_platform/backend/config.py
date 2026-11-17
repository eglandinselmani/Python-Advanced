"""Backend configuration, read from environment variables (.env supported)."""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def _secret_key() -> str:
    key = os.getenv("SECRET_KEY", "").strip()
    if key and not key.startswith("change-me"):
        return key
    # Generate once and persist so JWT tokens survive server restarts.
    f = DATA_DIR / ".secret_key"
    if not f.exists():
        f.write_text(secrets.token_urlsafe(48))
    return f.read_text().strip()


class Settings:
    APP_NAME = "Chartly Trading Platform API"
    SECRET_KEY = _secret_key()
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'trading.db'}")
    MARKET_DATA_MODE = os.getenv("MARKET_DATA_MODE", "auto")  # auto | simulated
    BACKGROUND_WORKER = os.getenv("BACKGROUND_WORKER", "1") == "1"
    STARTING_BALANCE = 100_000.0


settings = Settings()
