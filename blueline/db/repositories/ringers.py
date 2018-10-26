"""Ringers, and what they can ring."""

from __future__ import annotations

from typing import FrozenSet, List, Optional

from sqlalchemy import func

from blueline.core.ringers import Ringer
from blueline.db.base import Repository
from blueline.db.models import StoredRinger
from blueline.errors import LibraryError


def _lines(titles: FrozenSet[str]) -> str:
    """Titles as text, sorted so two equal sets store identically."""
    return "\n".join(sorted(titles))


def _titles(text: str) -> FrozenSet[str]:
    return frozenset(line.strip() for line in text.splitlines() if line.strip())


def to_stored_ringer(ringer: Ringer) -> StoredRinger:
    return StoredRinger(
        name=ringer.name.strip(),
        can_ring=_lines(ringer.can_ring),
        learning=_lines(ringer.learning),
    )


def to_ringer(stored: StoredRinger) -> Ringer:
    return Ringer(
        name=stored.name,
        can_ring=_titles(stored.can_ring),
        learning=_titles(stored.learning),
    )


class RingerRepository(Repository[StoredRinger]):
    """Ringers in the database."""

    model = StoredRinger

    def add(self, ringer: Ringer) -> StoredRinger:
        if self.find(ringer.name) is not None:
            raise LibraryError(f"{ringer.name} is already stored")
        return self.add_row(to_stored_ringer(ringer))

    def find(self, name: str) -> Optional[StoredRinger]:
        statement = self.session.query(StoredRinger).filter(
            func.lower(StoredRinger.name) == name.strip().lower()
        )
        return statement.one_or_none()

    def get(self, name: str) -> StoredRinger:
        found = self.find(name)
        if found is None:
            raise LibraryError(f"no ringer called {name!r} is stored")
        return found

    def save(self, ringer: Ringer) -> StoredRinger:
        """Store a ringer, replacing what was there under that name."""
        existing = self.find(ringer.name)
        if existing is None:
            return self.add(ringer)
        existing.can_ring = _lines(ringer.can_ring)
        existing.learning = _lines(ringer.learning)
        self.session.flush()
        return existing

    def remove(self, name: str) -> None:
        self.delete_row(self.get(name))

    def all(self) -> List[StoredRinger]:
        statement = self.session.query(StoredRinger).order_by(StoredRinger.name)
        return list(statement.all())

    def band(self) -> List[Ringer]:
        """Everybody, as the core's type."""
        return [to_ringer(stored) for stored in self.all()]

    def who_rings(self, title: str) -> List[StoredRinger]:
        """Everybody with this title among what they can ring.

        Matched on the stored text, which is titles separated by newlines, so
        this finds Cambridge Surprise Major and would also find it inside a
        longer title. The service checks properly; this narrows the query.
        """
        statement = (
            self.session.query(StoredRinger)
            .filter(StoredRinger.can_ring.ilike(f"%{title.strip()}%"))
            .order_by(StoredRinger.name)
        )
        return list(statement.all())
