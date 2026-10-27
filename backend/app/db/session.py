"""Database engine and session management.

PostgreSQL is the target database and is what Docker Compose provides. SQLite is
the zero-infrastructure fallback so the API starts immediately after a clone,
which matters more than it sounds: a reviewer should be able to run the service
without installing a database first.

The two differ in ways that bite, so both are handled explicitly rather than
hoped over. SQLite needs ``check_same_thread`` disabled for FastAPI's threadpool
and needs foreign keys switched on per connection, since it ignores them by
default. PostgreSQL gets connection pooling with pre-ping so a connection
dropped by the server is replaced rather than raising.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _build_engine() -> Engine:
    if settings.is_sqlite:
        path = settings.database_url.replace("sqlite:///", "")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(
            settings.database_url,
            echo=settings.sql_echo,
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record):  # type: ignore[no-untyped-def]
            # SQLite ignores foreign keys unless asked, which would let the
            # schema's referential integrity quietly stop applying in the
            # default development configuration.
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine

    return create_engine(
        settings.database_url,
        echo=settings.sql_echo,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=1800,
    )


engine: Engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a session that always closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
