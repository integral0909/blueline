"""Performances, and the towers and methods they point at."""

from __future__ import annotations

from typing import List, Optional


from blueline.core.bands import Band
from blueline.core.performance import Performance
from blueline.db.base import Repository
from blueline.db.models import StoredMethod, StoredPerformance, StoredTower
from blueline.errors import LibraryError


def to_stored_performance(
    performance: Performance,
    method: Optional[StoredMethod] = None,
    tower: Optional[StoredTower] = None,
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
        method: Optional[StoredMethod] = None,
        tower: Optional[StoredTower] = None,
    ) -> StoredPerformance:
        return self.add_row(to_stored_performance(performance, method, tower))

    def get(self, performance_id: int) -> StoredPerformance:
        found = self.get_by_id(performance_id)
        if found is None:
            raise LibraryError(f"no performance number {performance_id}")
        return found

    def search(
        self,
        place: Optional[str] = None,
        title: Optional[str] = None,
        stage: Optional[int] = None,
        min_length: Optional[int] = None,
        ringer: Optional[str] = None,
    ) -> List[StoredPerformance]:
        """Performances matching everything asked for, most recent first.

        A ringer is matched against the whole band as stored. That is a
        substring search over names separated by newlines, which finds Ann in
        a band that has her and also in one that has Annabel, and is what
        somebody typing a name into a box expects.
        """
        statement = self.session.query(StoredPerformance)
        if place is not None:
            statement = statement.filter(StoredPerformance.place.ilike(f"%{place.strip()}%"))
        if title is not None:
            statement = statement.filter(StoredPerformance.title.ilike(f"%{title.strip()}%"))
        if stage is not None:
            statement = statement.filter(StoredPerformance.stage == stage)
        if min_length is not None:
            statement = statement.filter(StoredPerformance.length >= min_length)
        if ringer is not None:
            statement = statement.filter(StoredPerformance.ringers.ilike(f"%{ringer.strip()}%"))
        statement = statement.order_by(
            StoredPerformance.rang_on.desc(), StoredPerformance.id.desc()
        )
        return list(statement.all())

    def all(self) -> List[StoredPerformance]:
        return self.search()

    def peals(self) -> List[StoredPerformance]:
        """Only the ones long enough to count as peals."""
        return [stored for stored in self.all() if to_performance(stored).is_peal]

    def places(self) -> List[str]:
        statement = self.session.query(StoredPerformance.place).distinct().order_by(StoredPerformance.place)
        return list(statement.all())
