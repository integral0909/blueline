import pytest

from blueline.db.session import (
    MEMORY_URL,
    create_all,
    drop_all,
    make_engine,
    session_factory,
)


@pytest.fixture()
def session():
    """A session on a fresh in memory database, rolled away afterwards."""
    engine = make_engine(MEMORY_URL)
    create_all(engine)
    factory = session_factory(engine)
    with factory() as opened:
        yield opened
    drop_all(engine)
