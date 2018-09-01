"""The migration has to describe the same schema the models do."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import inspect

from blueline.db.models import Base
from blueline.db.session import MEMORY_URL, create_all, make_engine

ROOT = Path(__file__).resolve().parent.parent.parent
VERSIONS = ROOT / "migrations" / "versions"


@pytest.fixture(scope="module")
def migration() -> str:
    """Every migration joined up.

    The checks are about what the schema ends up as, not about which revision
    put each piece there, and reading only the first one meant every table
    added afterwards looked missing.
    """
    return "\n".join(path.read_text() for path in sorted(VERSIONS.glob("*.py")))


class TestSetup:
    def test_alembic_is_configured(self):
        assert (ROOT / "alembic.ini").exists()

    def test_the_environment_reads_the_models(self):
        source = (ROOT / "migrations" / "env.py").read_text()
        assert "from blueline.db.models import Base" in source
        assert "target_metadata = Base.metadata" in source

    def test_batch_mode_is_on_for_sqlite(self):
        # Sqlite cannot alter a column in place without it.
        source = (ROOT / "migrations" / "env.py").read_text()
        assert source.count("render_as_batch=True") == 2


class TestInitialMigration:
    def test_it_is_the_first_one(self, migration):
        assert "down_revision = None" in migration

    def test_it_creates_both_tables(self, migration):
        assert '"methods"' in migration
        assert '"compositions"' in migration

    def test_it_can_be_undone(self, migration):
        assert "def downgrade()" in migration
        assert "op.drop_table" in migration

    def test_every_model_table_is_created(self, migration):
        for table in Base.metadata.tables:
            assert f'"{table}"' in migration

    def test_every_column_the_models_have_is_in_it(self, migration):
        for table in Base.metadata.tables.values():
            for column in table.columns:
                assert f'"{column.name}"' in migration, f"{table.name}.{column.name} missing"

    def test_the_cascade_is_declared(self, migration):
        assert 'ondelete="CASCADE"' in migration

    def test_the_title_is_unique(self, migration):
        assert "uq_methods_title" in migration


class TestAgainstTheModels:
    def test_the_models_build_the_same_table_names(self):
        engine = make_engine(MEMORY_URL)
        create_all(engine)
        assert set(inspect(engine).get_table_names()) == set(Base.metadata.tables)
