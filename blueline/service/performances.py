"""Recording and looking up what bands have rung.

Takes a band as a list of names and a date as a string, because that is what
comes off a form or a command line, and hands back a result rather than letting
a bad date out of the building.

The method is looked up where the title matches one in the library, and left
off where it does not. Somebody recording a peal of something the library has
never heard of should not be stopped, but where the method is known the link is
worth having.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from dataclasses import dataclass
from datetime import date

from blueline.core.bands import Band, band_of
from blueline.core.board import WIDTH, render
from blueline.core.performance import Performance
from blueline.core.statistics import Totals, leaderboard, totals_of
from blueline.db.models import StoredPerformance
from blueline.db.repositories import (
    MethodRepository,
    PerformanceRepository,
    TowerRepository,
    to_performance,
    to_tower,
)
from blueline.errors import BluelineError
from blueline.service.results import Result, invalid, not_found, succeeded


@dataclass(frozen=True)
class PerformanceView:
    """A performance as anybody wants to read it."""

    id: int
    title: str
    stage: int
    length: int
    rang_on: date
    place: str
    composer: Optional[str]
    conductor: str
    ringers: Tuple[str, ...]
    counts_as: str
    duration_minutes: int
    is_peal: bool
    has_covering_tenor: bool
    board: Tuple[str, ...]
    #: The tower, where the place matched one that is stored.
    tower: Optional[str] = None

    def summary(self) -> str:
        return f"{self.length} {self.title} at {self.place} on {self.rang_on:%d %B %Y}"


def parse_date(text: str) -> Result[date]:
    """Read a date written the way anybody would type it."""
    try:
        return succeeded(date.fromisoformat(text.strip()))
    except ValueError:
        return invalid(f"{text!r} is not a date, want something like 2023-03-18")


def make_band(names: List[str], conductor: Optional[str] = None) -> Result[Band]:
    try:
        return succeeded(band_of(names, conductor=conductor))
    except BluelineError as error:
        return invalid(str(error))


def view_of(stored: StoredPerformance) -> PerformanceView:
    performance = to_performance(stored)
    return PerformanceView(
        id=stored.id,
        title=performance.title,
        stage=performance.stage,
        length=performance.length,
        rang_on=performance.rang_on,
        place=performance.place,
        composer=performance.composer,
        conductor=performance.band.conducted_by,
        ringers=performance.band.ringers,
        counts_as=performance.standing.counts_as,
        duration_minutes=int(round(performance.duration.total_seconds() / 60)),
        is_peal=performance.is_peal,
        has_covering_tenor=performance.has_covering_tenor,
        board=tuple(performance.board()),
        tower=stored.tower.place if stored.tower else None,
    )


def record(
    performances: PerformanceRepository,
    methods: MethodRepository,
    title: str,
    stage: int,
    length: int,
    rang_on: str,
    place: str,
    ringers: List[str],
    conductor: Optional[str] = None,
    composer: Optional[str] = None,
    peal_speed: float = 30.0,
    towers: Optional[TowerRepository] = None,
) -> Result[PerformanceView]:
    """Write up something a band rang.

    Where the place matches a tower that is stored, the two are linked and the
    tower is checked. A ring of six cannot have rung major, and a performance
    saying it did is worth refusing rather than filing.
    """
    if peal_speed <= 0:
        return invalid("bells have to be rung at some speed")
    when = parse_date(rang_on)
    if not when.ok:
        return Result(failure=when.failure)
    band = make_band(ringers, conductor)
    if not band.ok:
        return Result(failure=band.failure)

    try:
        performance = Performance(
            band=band.unwrap(),
            title=title.strip(),
            stage=stage,
            length=length,
            rang_on=when.unwrap(),
            place=place.strip(),
            composer=composer,
            peal_speed=peal_speed,
        )
    except BluelineError as error:
        return invalid(str(error))

    at_tower = towers.find(place) if towers is not None else None
    if at_tower is not None and not to_tower(at_tower).rings(stage):
        return invalid(f"{at_tower.place} has {at_tower.bells} bells and cannot ring {stage}")

    stored = performances.add(performance, method=methods.find(title), tower=at_tower)
    return succeeded(view_of(stored))


def fetch(performances: PerformanceRepository, performance_id: int) -> Result[PerformanceView]:
    try:
        return succeeded(view_of(performances.get(performance_id)))
    except BluelineError:
        return not_found(f"no performance number {performance_id}")


def search(
    performances: PerformanceRepository,
    place: Optional[str] = None,
    title: Optional[str] = None,
    stage: Optional[int] = None,
    min_length: Optional[int] = None,
    ringer: Optional[str] = None,
) -> Result[List[PerformanceView]]:
    found = performances.search(
        place=place, title=title, stage=stage, min_length=min_length, ringer=ringer
    )
    return succeeded([view_of(stored) for stored in found])


def statistics(
    performances: PerformanceRepository,
    place: Optional[str] = None,
    ringer: Optional[str] = None,
) -> Result[Totals]:
    """Totals over the performances matching what was asked for.

    The same filters the listing takes, so a band can ask what they have rung
    at one tower rather than only what everybody has rung everywhere.
    """
    found = performances.search(place=place, ringer=ringer)
    return succeeded(totals_of([to_performance(stored) for stored in found]))


def top_ringers(
    performances: PerformanceRepository,
    top: int = 10,
) -> Result[List[Tuple[str, int]]]:
    totals = statistics(performances)
    if not totals.ok:
        return Result(failure=totals.failure)
    return succeeded(leaderboard(totals.unwrap().by_ringer, top=top))


def top_methods(
    performances: PerformanceRepository,
    top: int = 10,
) -> Result[List[Tuple[str, int]]]:
    totals = statistics(performances)
    if not totals.ok:
        return Result(failure=totals.failure)
    return succeeded(leaderboard(totals.unwrap().by_method, top=top))


def board(
    performances: PerformanceRepository,
    performance_id: int,
    width: int = WIDTH,
) -> Result[str]:
    """One performance laid out as it would be painted on a wall."""
    if width < 20:
        return invalid("a board narrower than twenty characters is unreadable")
    try:
        found = performances.get(performance_id)
    except BluelineError:
        return not_found(f"no performance number {performance_id}")
    return succeeded(str(render(to_performance(found), width=width)))
