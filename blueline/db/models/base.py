"""The declarative base, and the one thing every table shares.

Kept apart from the tables so a table can import it without importing every
other table, which is what makes splitting them by subject possible at all.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase


def now() -> datetime:
    """The current time, in UTC and with the zone attached.

    Naive datetimes in a database are a slow leak: everything works until two
    machines in different places disagree about what six o'clock meant.
    """
    return datetime.now(tz=UTC)


class Base(DeclarativeBase):
    pass
