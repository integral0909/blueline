"""Towers, taken from what somebody typed.

A weight comes in as text because that is how ringers write it, and a tower
that cannot ring what somebody is trying to record there is worth catching
before the performance goes in rather than afterwards.
"""

from __future__ import annotations

from typing import List, Optional

from dataclasses import dataclass

from blueline.core.towers import Tower, TowerError, Weight, parse_weight
from blueline.db.models import StoredTower
from blueline.db.repository import TowerRepository, to_tower
from blueline.errors import BluelineError
from blueline.service.results import Result, already_exists, invalid, not_found, succeeded


@dataclass(frozen=True)
class TowerView:
    """A tower as anybody wants to read it."""

    place: str
    bells: int
    tenor: str
    tenor_pounds: int
    is_heavy: bool
    rings_up_to: int

    def summary(self) -> str:
        heavy = ", a heavy ring" if self.is_heavy else ""
        return f"{self.place}, {self.bells} bells, tenor {self.tenor}{heavy}"


def view_of(stored: StoredTower) -> TowerView:
    tower = to_tower(stored)
    return TowerView(
        place=tower.place,
        bells=tower.bells,
        tenor=str(tower.tenor),
        tenor_pounds=tower.tenor.total_pounds,
        is_heavy=tower.is_heavy,
        rings_up_to=tower.bells,
    )


def make_tower(place: str, bells: int, tenor: str) -> Result[Tower]:
    """Build a tower from what somebody typed, weight and all."""
    try:
        weight: Weight = parse_weight(tenor)
        return succeeded(Tower(place=place, bells=bells, tenor=weight))
    except BluelineError as error:
        return invalid(str(error))


def add(repository: TowerRepository, place: str, bells: int, tenor: str) -> Result[TowerView]:
    built = make_tower(place, bells, tenor)
    if not built.ok:
        return Result(failure=built.failure)
    tower = built.unwrap()
    if repository.find(tower.place) is not None:
        return already_exists(f"{tower.place} is already stored")
    return succeeded(view_of(repository.add(tower)))


def fetch(repository: TowerRepository, place: str) -> Result[TowerView]:
    stored = repository.find(place)
    if stored is None:
        return not_found(f"no tower called {place!r}")
    return succeeded(view_of(stored))


def remove(repository: TowerRepository, place: str) -> Result[str]:
    stored = repository.find(place)
    if stored is None:
        return not_found(f"no tower called {place!r}")
    repository.remove(stored.place)
    return succeeded(stored.place)


def search(
    repository: TowerRepository,
    place: Optional[str] = None,
    min_bells: Optional[int] = None,
    max_bells: Optional[int] = None,
    min_tenor: Optional[str] = None,
) -> Result[List[TowerView]]:
    """Towers matching everything asked for, heaviest first."""
    pounds: Optional[int] = None
    if min_tenor is not None:
        try:
            pounds = parse_weight(min_tenor).total_pounds
        except TowerError as error:
            return invalid(str(error))
    found = repository.search(
        place=place, min_bells=min_bells, max_bells=max_bells, min_tenor_pounds=pounds
    )
    return succeeded([view_of(stored) for stored in found])


def can_ring(repository: TowerRepository, place: str, stage: int) -> Result[bool]:
    """Whether a stage can be rung at a tower."""
    stored = repository.find(place)
    if stored is None:
        return not_found(f"no tower called {place!r}")
    return succeeded(to_tower(stored).rings(stage))
