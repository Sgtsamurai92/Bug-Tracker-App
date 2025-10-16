from __future__ import annotations

from flask import Flask, g
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Global SQLAlchemy engine and session factory. Initialized in init_db(app).
engine = None  # type: object | None
SessionLocal = None  # type: sessionmaker | None


def init_db(app: Flask) -> None:
    """Initialize the database engine and session factory.

    Uses a file-based SQLite URL from app config. Registers a teardown
    hook to ensure request-scoped sessions are closed automatically.
    """
    global engine, SessionLocal
    db_url = f"sqlite:///{app.config['DATABASE']}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # Make sure sessions are closed after each request
    app.teardown_appcontext(close_db)


def get_db() -> Session:
    """Return the current request-scoped Session from flask.g.

    Lazily creates a Session on first access for the request and
    reuses it for subsequent calls. The session is closed at teardown.
    """
    if "db" not in g:
        # SessionLocal is initialized in init_db, so this should exist now
        g.db = SessionLocal()  # type: ignore[operator]
    return g.db  # type: ignore[return-value]


def close_db(e: Exception | None = None) -> None:
    """Teardown hook to close the request-scoped Session if present."""
    db: Session | None = g.pop("db", None)  # type: ignore[assignment]
    if db is not None:
        db.close()
