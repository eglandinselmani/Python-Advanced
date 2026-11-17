import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["MARKET_DATA_MODE"] = "simulated"   # tests never touch the internet
os.environ["BACKGROUND_WORKER"] = "0"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-0123456789"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from backend import database
from backend.main import app


def build_client(db_url: str):
    """Create an app wired to a specific SQLite file (used to simulate restarts)."""
    engine = database.make_engine(db_url)
    database.init_db(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[database.get_db] = override
    return TestClient(app), Session, engine


@pytest.fixture()
def client():
    with tempfile.TemporaryDirectory() as d:
        c, _, engine = build_client(f"sqlite:///{d}/test.db")
        yield c
        engine.dispose()
        app.dependency_overrides.clear()


def register_and_login(c, username="alice", password="Passw0rd123", email=None):
    r = c.post("/api/auth/register", json={"username": username, "email": email or f"{username}@example.com",
                                             "password": password})
    assert r.status_code == 201, r.text
    t = c.post("/api/auth/login", json={"username": username, "password": password})
    assert t.status_code == 200, t.text
    return {"Authorization": f"Bearer {t.json()['access_token']}"}


@pytest.fixture()
def auth(client):
    return register_and_login(client)
