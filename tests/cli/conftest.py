import pytest
from typer.testing import CliRunner

from blueline.api import deps
from blueline.db.repository import MethodRepository
from blueline.db.seed import seed_standard
from blueline.db.session import MEMORY_URL, create_all, make_engine, session_factory


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def library():
    """Point the command line at a fresh in memory database."""
    engine = make_engine(MEMORY_URL)
    create_all(engine)
    deps._engine = engine
    deps._factory = session_factory(engine)
    return deps._factory


@pytest.fixture()
def seeded(library):
    with library() as session:
        seed_standard(MethodRepository(session))
        session.commit()
    return library
