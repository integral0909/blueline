"""Planning a practice from what is in the library.

Takes a band size and an hour and hands back what they could ring, using the
methods that are actually stored rather than a fixed list. A tower that has
added its own methods should see them in the plan.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from dataclasses import dataclass

from blueline.core.plans import Item, PlanError, plan_practice, ringable_by
from blueline.db.repository import MethodRepository, TowerRepository, to_method, to_tower
from blueline.errors import BluelineError
from blueline.service.results import Result, invalid, not_found, succeeded


@dataclass(frozen=True)
class PlanView:
    """An evening's ringing, as anybody wants to read it."""

    ringers: int
    minutes: int
    used_minutes: int
    spare_minutes: int
    changes: int
    items: Tuple[str, ...]
    titles: Tuple[str, ...]
    summary: str


def _view(
    items: Tuple[Item, ...], ringers: int, minutes: int, spare: int, changes: int, summary: str
) -> PlanView:
    return PlanView(
        ringers=ringers,
        minutes=minutes,
        used_minutes=sum(item.minutes for item in items),
        spare_minutes=spare,
        changes=changes,
        items=tuple(str(item) for item in items),
        titles=tuple(item.title for item in items),
        summary=summary,
    )


def plan(
    repository: MethodRepository,
    ringers: int,
    minutes: int,
    speed: float = 30.0,
    towers: Optional[TowerRepository] = None,
    place: Optional[str] = None,
) -> Result[PlanView]:
    """What a band could ring in the time, out of what is stored.

    Where a tower is named, its bells cap the plan as well as the band. Eight
    people in a ring of six are still ringing minor.
    """
    if speed <= 0:
        return invalid("bells have to be rung at some speed")

    at_most = ringers
    if place is not None:
        if towers is None:
            return invalid("no towers are stored to look that up in")
        stored = towers.find(place)
        if stored is None:
            return not_found(f"no tower called {place!r}")
        at_most = min(ringers, to_tower(stored).bells)

    methods = [to_method(each) for each in repository.all()]
    try:
        made = plan_practice(methods, ringers=at_most, minutes=minutes, speed=speed)
    except (PlanError, BluelineError) as error:
        return invalid(str(error))

    spare = int(round(made.left_over.total_seconds() / 60))
    return succeeded(_view(made.items, at_most, minutes, spare, made.changes, made.summary()))


def what_can_be_rung(repository: MethodRepository, ringers: int) -> Result[List[str]]:
    """The titles a band of this size could ring, without planning anything."""
    methods = [to_method(each) for each in repository.all()]
    try:
        found = ringable_by(methods, ringers)
    except PlanError as error:
        return invalid(str(error))
    return succeeded(sorted(f"{method.name} {method.stage}" for method in found))
