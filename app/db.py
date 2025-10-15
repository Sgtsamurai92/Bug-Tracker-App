from __future__ import annotations
from typing import Optional

from flask import Flask, g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

engine = None  # type: Optional[object]
SessionLocal = None  # type: Optional[sessionmaker]


def init_db(app: Flask) -> None:
    global engine, SessionLocal
    db_url = f"sqlite:///{app.config['DATABASE']}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # Make sure sessions are closed after each request
    app.teardown_appcontext(close_db)


def get_db() -> Session:
    if "db" not in g:
        # SessionLocal is initialized in init_db, so this should exist now
        g.db = SessionLocal()  # type: ignore[operator]
    return g.db  # type: ignore[return-value]


def close_db(e: Exception | None = None) -> None:
    db: Session | None = g.pop("db", None)  # type: ignore[assignment]
    if db is not None:
        db.close()
