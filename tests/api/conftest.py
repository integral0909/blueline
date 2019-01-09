import pytest
from blueline.api.testing import Client

from blueline.api import deps
from blueline.api.app import create_app
from blueline.config import Settings
from blueline.db.session import MEMORY_URL, create_all, drop_all, make_engine, session_factory


@pytest.fixture()
def client():
    """A client on an application pointed at a fresh in memory database."""
    deps.reset()
    yield Client(create_app(Settings(database_url=MEMORY_URL)))
    deps.reset()


@pytest.fixture()
def seeded():
    """The same client, with the standard methods already stored."""
    deps.reset()
    yield Client(create_app(Settings(database_url=MEMORY_URL, seed_on_start=True)))
    deps.reset()


@pytest.fixture()
def session():
    """A session on a database that vanishes afterwards.

    For the tests that build a repository directly rather than going through
    a request.
    """
    engine = make_engine(MEMORY_URL)
    create_all(engine)
    factory = session_factory(engine)
    opened = factory()
    try:
        yield opened
    finally:
        opened.close()
    drop_all(engine)
