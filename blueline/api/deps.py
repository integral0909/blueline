"""What the handlers need, handed to them rather than reached for.

A handler that opened its own session would be untestable without a database
and would decide the transaction boundary halfway down a call stack. FastAPI's
dependency mechanism gives the session to the handler and closes it afterwards,
and a test can override the whole thing with something pointing at memory.

Configuring goes through a Settings rather than through arguments that had
started to multiply. The command line configures the same way, so the two
cannot end up talking to different databases.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from blueline.config import Settings, load
from blueline.db.repositories import MethodRepository
from blueline.db.seed import seed_standard
from blueline.db.session import create_all, make_engine, session_factory

_engine: Engine | None = None
_factory: sessionmaker[Session] | None = None
_settings: Settings | None = None


def configure(settings: Settings | None = None) -> Settings:
    """Point the application at a database. Called once, at startup."""
    global _engine, _factory, _settings
    _settings = settings or load()
    _engine = make_engine(_settings.database_url, echo=_settings.echo_sql)
    if _settings.create_tables:
        create_all(_engine)
    _factory = session_factory(_engine)
    if _settings.seed_on_start:
        session = _factory()
        try:
            seed_standard(MethodRepository(session))
            session.commit()
        finally:
            session.close()
    return _settings


def get_settings() -> Settings:
    if _settings is None:
        configure()
    assert _settings is not None
    return _settings


def get_factory() -> sessionmaker[Session]:
    if _factory is None:
        configure()
    assert _factory is not None
    return _factory


def reset() -> None:
    """Forget what we were pointed at, so a test can point somewhere else."""
    global _engine, _factory, _settings
    _engine = None
    _factory = None
    _settings = None


def get_session() -> Iterator[Session]:
    """A session, committed if the caller did not throw.

    The http layer opens its own per request; this is for the command line
    and for anything else that wants one outside a request."""
    session = get_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_methods(session: Session) -> MethodRepository:
    return MethodRepository(session)
