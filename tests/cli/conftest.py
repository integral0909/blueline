import pytest
from click.testing import CliRunner

from blueline.api import deps
from blueline.config import Settings
from blueline.db.session import MEMORY_URL


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def library():
    """Point the command line at a fresh in memory database."""
    deps.reset()
    deps.configure(Settings(database_url=MEMORY_URL))
    yield deps.get_factory()
    deps.reset()


@pytest.fixture()
def seeded():
    """The same, with the standard methods already loaded."""
    deps.reset()
    deps.configure(Settings(database_url=MEMORY_URL, seed_on_start=True))
    yield deps.get_factory()
    deps.reset()
