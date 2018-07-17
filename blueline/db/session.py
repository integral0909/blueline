"""Getting hold of a database session.

Kept apart from the models so tests can point at an in memory database without
the models knowing anything about it. Everything that touches the database
takes a session rather than reaching for a global one, which is what makes it
possible to run a test inside a transaction and roll it back afterwards.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from blueline.db.models import Base

DEFAULT_URL = "sqlite+pysqlite:///blueline.db"
MEMORY_URL = "sqlite+pysqlite:///:memory:"


def make_engine(url: str = DEFAULT_URL, echo: bool = False) -> Engine:
    """Build an engine, telling sqlite to behave itself about foreign keys."""
    engine = create_engine(url, echo=echo, future=True)
    if url.startswith("sqlite"):
        from sqlalchemy import event

        @event.listens_for(engine, "connect")
        def _set_pragma(connection, _record):  # type: ignore[no-untyped-def]
            # Sqlite ignores foreign keys unless asked, which turns a cascade
            # into a pile of orphaned rows nobody notices until much later.
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def create_all(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def drop_all(engine: Engine) -> None:
    Base.metadata.drop_all(engine)


def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """A session that commits on the way out, or rolls back if anything threw."""
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
