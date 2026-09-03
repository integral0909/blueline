"""Rings of bells."""

from __future__ import annotations

from sqlalchemy import func, select

from blueline.core.towers import Tower, weight_from_pounds
from blueline.db.base import Repository
from blueline.db.models import StoredTower
from blueline.errors import LibraryError


def to_stored_tower(tower: Tower) -> StoredTower:
    return StoredTower(
        place=tower.place.strip(),
        bells=tower.bells,
        tenor_pounds=tower.tenor.total_pounds,
    )


def to_tower(stored: StoredTower) -> Tower:
    return Tower(
        place=stored.place,
        bells=stored.bells,
        tenor=weight_from_pounds(stored.tenor_pounds),
    )


class TowerRepository(Repository[StoredTower]):
    """Towers in the database."""

    model = StoredTower

    def add(self, tower: Tower) -> StoredTower:
        if self.find(tower.place) is not None:
            raise LibraryError(f"{tower.place} is already stored")
        return self.add_row(to_stored_tower(tower))

    def find(self, place: str) -> StoredTower | None:
        statement = select(StoredTower).where(
            func.lower(StoredTower.place) == place.strip().lower()
        )
        return self.session.scalars(statement).one_or_none()

    def get(self, place: str) -> StoredTower:
        found = self.find(place)
        if found is None:
            raise LibraryError(f"no tower called {place!r} is stored")
        return found

    def remove(self, place: str) -> None:
        self.delete_row(self.get(place))

    def search(
        self,
        place: str | None = None,
        min_bells: int | None = None,
        max_bells: int | None = None,
        min_tenor_pounds: int | None = None,
    ) -> list[StoredTower]:
        """Towers matching everything asked for, heaviest first.

        Heaviest first because that is the order anybody browsing a list of
        towers wants them: the notable ones at the top.
        """
        statement = select(StoredTower)
        if place is not None:
            statement = statement.where(StoredTower.place.ilike(f"%{place.strip()}%"))
        if min_bells is not None:
            statement = statement.where(StoredTower.bells >= min_bells)
        if max_bells is not None:
            statement = statement.where(StoredTower.bells <= max_bells)
        if min_tenor_pounds is not None:
            statement = statement.where(StoredTower.tenor_pounds >= min_tenor_pounds)
        statement = statement.order_by(StoredTower.tenor_pounds.desc(), StoredTower.place)
        return list(self.session.scalars(statement).all())

    def all(self) -> list[StoredTower]:
        return self.search()

    def able_to_ring(self, stage: int) -> list[StoredTower]:
        """Towers with enough bells for a stage."""
        return self.search(min_bells=stage)
