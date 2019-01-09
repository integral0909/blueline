"""What every repository does the same way.

Three of them had grown the same count, the same all, and the same holding of
a session, and the counts had already been written two different ways. The
searching cannot be shared, because what a method matches on and what a
performance matches on have nothing to do with each other, and that is the part
worth keeping separate anyway.
"""

from __future__ import annotations

from typing import Generic, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from blueline.db.models import Base

Row = TypeVar("Row", bound=Base)


class Repository(Generic[Row]):
    """A table, and a session to reach it through.

    The session is taken rather than opened. Where a transaction starts and
    ends belongs to the caller, and a repository that committed on its own
    would make it impossible to store a method and its compositions together.
    """

    #: The mapped class this repository is for.
    model: Type[Row]

    def __init__(self, session: Session) -> None:
        self.session = session

    def count(self) -> int:
        return self.session.query(self.model).count()

    def get_by_id(self, row_id: int) -> Optional[Row]:
        return self.session.query(self.model).get(row_id)

    def add_row(self, row: Row) -> Row:
        """Put a row in and give it back with its id filled in."""
        self.session.add(row)
        self.session.flush()
        return row

    def delete_row(self, row: Row) -> None:
        self.session.delete(row)
