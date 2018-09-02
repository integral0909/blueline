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
from blueline.core.performance import Performance
from blueline.db.models import StoredPerformance
from blueline.db.repository import (
    MethodRepository,
    PerformanceRepository,
    to_performance,
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
    is_peal: bool
    has_covering_tenor: bool
    board: Tuple[str, ...]

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
        is_peal=performance.is_peal,
        has_covering_tenor=performance.has_covering_tenor,
        board=tuple(performance.board()),
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
) -> Result[PerformanceView]:
    """Write up something a band rang."""
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
        )
    except BluelineError as error:
        return invalid(str(error))

    stored = performances.add(performance, method=methods.find(title))
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
