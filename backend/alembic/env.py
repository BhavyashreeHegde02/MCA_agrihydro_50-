"""Alembic environment.

Two things here are not boilerplate.

**The URL comes from the application's settings**, not from alembic.ini. A
migration that can target a different database than the service does is a
migration that will eventually be applied to the wrong one, and a connection
string in a committed file is a secret waiting to leak.

**SQLite gets batch mode.** SQLite cannot ALTER a column, drop a constraint or
add one to an existing table; it has to rewrite the table and copy the rows.
Alembic does that under ``render_as_batch``, and without it every migration
beyond the first would fail on the development database while passing on
PostgreSQL - the worst possible split, because the failure would only appear
on the machine that has no DBA.
"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, event, pool

# The application package, imported the way uvicorn imports it.
_BACKEND = Path(__file__).resolve().parent.parent
_ROOT = _BACKEND.parent
for candidate in (str(_ROOT), str(_BACKEND)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from app.core.config import settings  # noqa: E402
from app.db.models import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Autogenerate compares the live database against this.
target_metadata = Base.metadata

config.set_main_option("sqlalchemy.url", settings.database_url)


def _is_sqlite() -> bool:
    return settings.database_url.startswith("sqlite")


def run_migrations_offline() -> None:
    """Emit SQL to stdout without connecting.

    Useful for handing a DBA the statements to review before they are run
    against a production database.
    """
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=_is_sqlite(),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations against a live connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    if _is_sqlite():
        # SQLite ignores foreign keys unless asked, once per connection. A
        # migration that rewrites tables needs them enforced, or a broken
        # reference survives the upgrade silently.
        #
        # This is an engine-level listener rather than a statement on the
        # connection, and that matters. Executing anything on the connection
        # before context.configure() opens an implicit transaction under
        # SQLAlchemy 2.0; Alembic then finds itself already inside one, its own
        # begin_transaction() becomes a no-op, and nothing is ever committed.
        # The tables appear, the alembic_version row does not, and every
        # subsequent command reports the database as not up to date.
        @event.listens_for(connectable, "connect")
        def _enable_foreign_keys(dbapi_connection, _record):  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Without these, a changed column type or default is invisible to
            # autogenerate and quietly drifts out of the migration history.
            compare_type=True,
            compare_server_default=True,
            render_as_batch=_is_sqlite(),
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
