import pytest
from fastapi.testclient import TestClient

from blueline.api import deps
from blueline.api.app import create_app
from blueline.config import Settings
from blueline.db.session import MEMORY_URL


@pytest.fixture()
def client():
    """A client on an application pointed at a fresh in memory database."""
    deps.reset()
    app = create_app(Settings(database_url=MEMORY_URL))
    with TestClient(app) as opened:
        yield opened
    deps.reset()


@pytest.fixture()
def seeded():
    """The same client, with the standard methods already stored."""
    deps.reset()
    app = create_app(Settings(database_url=MEMORY_URL, seed_on_start=True))
    with TestClient(app) as opened:
        yield opened
    deps.reset()
