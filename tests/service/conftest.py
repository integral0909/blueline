import pytest

from blueline.db.repository import MethodRepository, PerformanceRepository
from blueline.db.session import MEMORY_URL, create_all, drop_all, make_engine, session_factory
from blueline.library.builtin import standard_methods


@pytest.fixture()
def repository():
    engine = make_engine(MEMORY_URL)
    create_all(engine)
    factory = session_factory(engine)
    with factory() as session:
        yield MethodRepository(session)
    drop_all(engine)


@pytest.fixture()
def loaded(repository):
    """A repository with the standard set already in it."""
    for method in standard_methods():
        repository.add(method)
    return repository


@pytest.fixture()
def performances(repository):
    """A performance repository on the same session as the method one."""
    return PerformanceRepository(repository.session)
