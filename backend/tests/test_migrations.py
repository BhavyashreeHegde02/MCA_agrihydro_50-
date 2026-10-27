"""The migration history, checked against the models it claims to build.

A migration and a model file can disagree in a way nothing else notices. The
application creates its schema with ``create_all`` in development, so the
models are what a developer sees; a deployment runs ``alembic upgrade head``,
so the migration is what production gets. If those two drift, every test still
passes and the difference only appears once, in the environment that matters.

These tests close that gap. They run the migration against a real empty
database and compare the result with what the models describe.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.db.models import Base

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def _alembic_config(database_url: str) -> Config:
    config = Config(str(ALEMBIC_INI))
    # env.py reads the URL from application settings, so it is overridden here
    # rather than in the ini, which carries no connection string by design.
    config.set_main_option("sqlalchemy.url", database_url)
    return config


@pytest.fixture
def migrated_url(tmp_path: Path, monkeypatch) -> str:
    """An empty database brought up entirely by the migration history."""
    path = tmp_path / "migrated.db"
    url = f"sqlite:///{path.as_posix()}"

    # env.py resolves the URL through the cached settings object, so the
    # environment has to change before it is read.
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "database_url", url, raising=False)
    command.upgrade(_alembic_config(url), "head")
    return url


class TestMigrationBuildsTheSchema:
    def test_upgrade_creates_every_table_the_models_declare(
        self, migrated_url: str
    ) -> None:
        engine = create_engine(migrated_url)
        try:
            actual = set(inspect(engine).get_table_names()) - {"alembic_version"}
        finally:
            engine.dispose()

        expected = set(Base.metadata.tables)
        missing = expected - actual
        extra = actual - expected
        assert not missing, f"the migration does not create {sorted(missing)}"
        assert not extra, f"the migration creates tables no model declares: {sorted(extra)}"

    def test_every_required_entity_is_present(self, migrated_url: str) -> None:
        # The entities the project specification names. Listed explicitly so a
        # table quietly disappearing from the models fails here too.
        required = {
            "users", "farmers", "farms", "fields", "crops", "crop_varieties",
            "crop_growth_stages", "field_crops", "soil_data", "district_soil_map",
            "weather_data", "predictions", "irrigation_records", "water_use",
            "model_versions", "data_quality_alerts", "advisories",
        }
        engine = create_engine(migrated_url)
        try:
            actual = set(inspect(engine).get_table_names())
        finally:
            engine.dispose()
        assert required <= actual, f"missing {sorted(required - actual)}"

    def test_columns_match_the_models(self, migrated_url: str) -> None:
        engine = create_engine(migrated_url)
        try:
            inspector = inspect(engine)
            for name, table in Base.metadata.tables.items():
                migrated = {c["name"] for c in inspector.get_columns(name)}
                declared = {c.name for c in table.columns}
                assert declared == migrated, (
                    f"{name}: models declare {sorted(declared - migrated)} that the "
                    f"migration omits, and the migration adds "
                    f"{sorted(migrated - declared)}"
                )
        finally:
            engine.dispose()

    def test_foreign_keys_survive_the_migration(self, migrated_url: str) -> None:
        # Referential integrity is the part most easily lost when a migration
        # is hand-edited, and SQLite will happily run without it.
        engine = create_engine(migrated_url)
        try:
            inspector = inspect(engine)
            for name, table in Base.metadata.tables.items():
                declared = len(table.foreign_keys)
                migrated = len(inspector.get_foreign_keys(name))
                assert migrated >= declared, (
                    f"{name}: models declare {declared} foreign keys, "
                    f"the migration created {migrated}"
                )
        finally:
            engine.dispose()

    def test_unique_constraints_survive_the_migration(self, migrated_url: str) -> None:
        engine = create_engine(migrated_url)
        try:
            inspector = inspect(engine)
            for name in ("users", "crops", "water_use", "crop_varieties",
                         "district_soil_map"):
                if name not in Base.metadata.tables:
                    continue
                constraints = inspector.get_unique_constraints(name)
                indexes = [i for i in inspector.get_indexes(name) if i.get("unique")]
                assert constraints or indexes, f"{name} lost its uniqueness guarantee"
        finally:
            engine.dispose()


class TestMigrationMatchesTheModels:
    def test_autogenerate_finds_nothing_left_to_do(self, migrated_url: str) -> None:
        """The check that actually prevents drift.

        After upgrading, Alembic compares the live schema against the models.
        Anything it would still want to change is, by definition, a difference
        between what a deployment gets and what a developer sees.
        """
        from alembic.autogenerate import compare_metadata
        from alembic.migration import MigrationContext

        engine = create_engine(migrated_url)
        try:
            with engine.connect() as connection:
                context = MigrationContext.configure(
                    connection,
                    opts={"compare_type": True, "compare_server_default": True},
                )
                differences = compare_metadata(context, Base.metadata)
        finally:
            engine.dispose()

        assert differences == [], f"migration and models disagree: {differences}"

    def test_the_revision_is_recorded(self, migrated_url: str) -> None:
        # The tables appearing is not proof the migration ran: a partially
        # committed upgrade leaves the schema in place and alembic_version
        # empty, and every later command then reports the database as behind.
        path = migrated_url.replace("sqlite:///", "")
        with sqlite3.connect(path) as connection:
            rows = list(connection.execute("select version_num from alembic_version"))
        assert len(rows) == 1, "exactly one revision should be stamped"
        assert rows[0][0]


class TestMigrationIsReversible:
    def test_downgrade_removes_everything_it_created(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        path = tmp_path / "reversible.db"
        url = f"sqlite:///{path.as_posix()}"
        from app.core import config as config_module

        monkeypatch.setattr(config_module.settings, "database_url", url, raising=False)
        config = _alembic_config(url)

        command.upgrade(config, "head")
        engine = create_engine(url)
        try:
            after_upgrade = set(inspect(engine).get_table_names())
        finally:
            engine.dispose()
        assert len(after_upgrade) > 15

        command.downgrade(config, "base")
        engine = create_engine(url)
        try:
            after_downgrade = set(inspect(engine).get_table_names())
        finally:
            engine.dispose()

        # Only Alembic's own bookkeeping table should remain.
        assert after_downgrade <= {"alembic_version"}, (
            f"downgrade left {sorted(after_downgrade - {'alembic_version'})} behind"
        )

    def test_the_round_trip_is_repeatable(self, tmp_path: Path, monkeypatch) -> None:
        # A downgrade that cannot be followed by another upgrade is not a
        # rollback path, it is a one-way door.
        path = tmp_path / "roundtrip.db"
        url = f"sqlite:///{path.as_posix()}"
        from app.core import config as config_module

        monkeypatch.setattr(config_module.settings, "database_url", url, raising=False)
        config = _alembic_config(url)

        command.upgrade(config, "head")
        command.downgrade(config, "base")
        command.upgrade(config, "head")

        engine = create_engine(url)
        try:
            tables = set(inspect(engine).get_table_names()) - {"alembic_version"}
        finally:
            engine.dispose()
        assert tables == set(Base.metadata.tables)


class TestMigrationHistory:
    def test_there_is_exactly_one_head(self) -> None:
        # Two heads mean two people added a migration against the same parent,
        # and `upgrade head` will refuse to choose between them.
        from alembic.script import ScriptDirectory

        script = ScriptDirectory.from_config(_alembic_config("sqlite://"))
        heads = script.get_heads()
        assert len(heads) == 1, f"the history has branched: {heads}"

    def test_every_revision_can_be_walked_from_base(self) -> None:
        from alembic.script import ScriptDirectory

        script = ScriptDirectory.from_config(_alembic_config("sqlite://"))
        revisions = list(script.walk_revisions())
        assert revisions, "no migrations exist"
        # The oldest revision must be rooted, or the chain starts nowhere.
        assert revisions[-1].down_revision is None

    def test_every_migration_defines_both_directions(self) -> None:
        from alembic.script import ScriptDirectory

        script = ScriptDirectory.from_config(_alembic_config("sqlite://"))
        for revision in script.walk_revisions():
            source = Path(revision.path).read_text(encoding="utf-8")
            assert "def upgrade()" in source, f"{revision.revision} cannot be applied"
            assert "def downgrade()" in source, f"{revision.revision} cannot be undone"
