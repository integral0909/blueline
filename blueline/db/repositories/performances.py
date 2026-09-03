"""Performances, and the towers and methods they point at."""

from __future__ import annotations

from sqlalchemy import select

from blueline.core.bands import Band
from blueline.core.performance import Performance
from blueline.db.base import Repository
from blueline.db.models import StoredMethod, StoredPerformance, StoredTower
from blueline.errors import LibraryError


def to_stored_performance(
    performance: Performance,
    method: StoredMethod | None = None,
    tower: StoredTower | None = None,
) -> StoredPerformance:
    """Flatten a performance for storing, band and all."""
    return StoredPerformance(
        method=method,
        tower=tower,
        title=performance.title.strip(),
        stage=performance.stage,
        length=performance.length,
        rang_on=performance.rang_on,
        place=performance.place.strip(),
        composer=performance.composer,
        peal_speed=performance.peal_speed,
        ringers="\n".join(name.strip() for name in performance.band.ringers),
        conductor=performance.band.conductor,
    )


def to_performance(stored: StoredPerformance) -> Performance:
    """Rebuild a performance from what was stored."""
    return Performance(
        band=Band(
            ringers=tuple(stored.ringers.splitlines()),
            conductor=stored.conductor,
        ),
        title=stored.title,
        stage=stored.stage,
        length=stored.length,
        rang_on=stored.rang_on,
        place=stored.place,
        composer=stored.composer,
        peal_speed=stored.peal_speed,
    )


class PerformanceRepository(Repository[StoredPerformance]):
    """Performances in the database."""

    model = StoredPerformance

    def add(
        self,
        performance: Performance,
        method: StoredMethod | None = None,
        tower: StoredTower | None = None,
    ) -> StoredPerformance:
        return self.add_row(to_stored_performance(performance, method, tower))

    def get(self, performance_id: int) -> StoredPerformance:
        found = self.get_by_id(performance_id)
        if found is None:
            raise LibraryError(f"no performance number {performance_id}")
        return found

    def search(
        self,
        place: str | None = None,
        title: str | None = None,
        stage: int | None = None,
        min_length: int | None = None,
        ringer: str | None = None,
    ) -> list[StoredPerformance]:
        """Performances matching everything asked for, most recent first.

        A ringer is matched against the whole band as stored. That is a
        substring search over names separated by newlines, which finds Ann in
        a band that has her and also in one that has Annabel, and is what
        somebody typing a name into a box expects.
        """
        statement = select(StoredPerformance)
        if place is not None:
            statement = statement.where(StoredPerformance.place.ilike(f"%{place.strip()}%"))
        if title is not None:
            statement = statement.where(StoredPerformance.title.ilike(f"%{title.strip()}%"))
        if stage is not None:
            statement = statement.where(StoredPerformance.stage == stage)
        if min_length is not None:
            statement = statement.where(StoredPerformance.length >= min_length)
        if ringer is not None:
            statement = statement.where(StoredPerformance.ringers.ilike(f"%{ringer.strip()}%"))
        statement = statement.order_by(
            StoredPerformance.rang_on.desc(), StoredPerformance.id.desc()
        )
        return list(self.session.scalars(statement).all())

    def all(self) -> list[StoredPerformance]:
        return self.search()

    def peals(self) -> list[StoredPerformance]:
        """Only the ones long enough to count as peals."""
        return [stored for stored in self.all() if to_performance(stored).is_peal]

    def places(self) -> list[str]:
        statement = select(StoredPerformance.place).distinct().order_by(StoredPerformance.place)
        return list(self.session.scalars(statement).all())
