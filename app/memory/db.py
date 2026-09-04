"""
Database engine and session factory.

Uses SQLite by default (DATABASE_URL from settings).
PostgreSQL-ready: swap DATABASE_URL to a postgres:// URI, no code changes needed.

Usage (anywhere in the app):
    from app.memory.db import get_session
    with get_session() as session:
        session.add(...)
        session.commit()

Call `init_db()` once at startup (done in app/api/main.py lifespan).
"""
from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.memory.models import Base

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            # Enable WAL mode and foreign keys for SQLite
            connect_args = {"check_same_thread": False}
        _engine = create_engine(settings.database_url, connect_args=connect_args)

        if settings.database_url.startswith("sqlite"):
            @event.listens_for(_engine, "connect")
            def set_sqlite_pragma(dbapi_conn, _connection_record):
                try:
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    # In serverless environments, WAL may not be supported on /tmp
                    if not (os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")):
                        cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.close()
                except Exception:
                    pass

    return _engine


def init_db() -> None:
    """Create all tables if they don't exist. Safe to call on every startup."""
    Base.metadata.create_all(bind=get_engine())


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context-manager session — commits on clean exit, rolls back on exception."""
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
