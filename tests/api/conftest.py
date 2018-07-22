import pytest
from fastapi.testclient import TestClient

from blueline.api import deps
from blueline.api.app import create_app
from blueline.db.repository import MethodRepository
from blueline.db.seed import seed_standard
from blueline.db.session import MEMORY_URL, create_all, make_engine, session_factory


@pytest.fixture()
def client():
    """A client on an application pointed at a fresh in memory database.

    Sqlite drops an in memory database when the last connection to it closes,
    so the engine is held for the whole test rather than being made per
    request.
    """
    engine = make_engine(MEMORY_URL)
    create_all(engine)
    factory = session_factory(engine)
    deps._engine = engine
    deps._factory = factory
    app = create_app()
    with TestClient(app) as opened:
        yield opened


@pytest.fixture()
def seeded(client):
    """The same client, with the standard methods already stored."""
    factory = deps.get_factory()
    with factory() as session:
        seed_standard(MethodRepository(session))
        session.commit()
    return client
