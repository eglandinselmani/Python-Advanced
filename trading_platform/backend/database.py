"""SQLAlchemy engine, session factory and declarative base."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings


class Base(DeclarativeBase):
    pass


def make_engine(url: str):
    kwargs = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    eng = create_engine(url, **kwargs)
    if url.startswith("sqlite"):
        @event.listens_for(eng, "connect")
        def _fk(dbapi_conn, _):  # enforce foreign keys in SQLite
            dbapi_conn.execute("PRAGMA foreign_keys=ON")
    return eng


engine = make_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(bind=None):
    from backend import models  # noqa: F401  (register tables)
    Base.metadata.create_all(bind=bind or engine)
