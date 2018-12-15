"""A tower's report for the year.

Every tower writes one, and every tower writes it by hand out of four different
notebooks the week before the AGM. Everything it needs is already stored: what
was rung, who rang it, what the band can ring between them, and how the
competition went.

The year is the calendar year rather than anything ecclesiastical. A tower AGM
happens whenever the tower feels like it and reporting against a movable year
would mean two reports never covering the same span.

Nothing is stored. A report is a document produced from what is already there,
and a stored one would go stale the moment somebody entered a performance they
had forgotten about.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from dataclasses import dataclass
from datetime import date

from blueline.core.calendar import occasions
from blueline.core.statistics import Totals
from blueline.db.repositories import (
    CollectionRepository,
    CompetitionRepository,
    MethodRepository,
    PerformanceRepository,
    RingerRepository,
    to_competition,
)
from blueline.service.collections import coverage
from blueline.service.performances import statistics
from blueline.service.results import Result, invalid, succeeded

#: Nothing before bells were hung in rings, and nothing implausibly far ahead.
FIRST_YEAR = 1600


@dataclass(frozen=True)
class CompetitionLine:
    """How the tower did in one competition."""

    name: str
    when: date
    entered: bool
    position: Optional[int]
    bands: int

    def __str__(self) -> str:
        if not self.entered:
            return f"{self.name}: did not enter"
        return f"{self.name}: {self.position} of {self.bands}"


@dataclass(frozen=True)
class AnnualView:
    """A tower's year."""

    year: int
    place: str
    totals: Totals
    peals: int
    quarters: int
    other: int
    changes: int
    ringers: int
    top_ringers: Tuple[Tuple[str, int], ...]
    top_methods: Tuple[Tuple[str, int], ...]
    competitions: Tuple[CompetitionLine, ...]
    repertoire: int
    covers: float
    occasions_rung: Tuple[str, ...]

    @property
    def quiet(self) -> bool:
        return self.totals.performances == 0

    def summary(self) -> str:
        if self.quiet:
            return f"{self.place}, {self.year}: nothing rung"
        return (
            f"{self.place}, {self.year}: {self.totals.performances} performances, "
            f"{self.peals} peals, {self.quarters} quarters"
        )


def _leaders(counts: Dict[str, int], top: int) -> Tuple[Tuple[str, int], ...]:
    ordered = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    return tuple(ordered[:top])


def report(
    performances: PerformanceRepository,
    ringers: RingerRepository,
    competitions: CompetitionRepository,
    collections: CollectionRepository,
    methods: MethodRepository,
    year: int,
    place: str,
    against: str = "the standard eight",
    top: int = 5,
) -> Result[AnnualView]:
    """Everything a tower puts in front of its AGM."""
    if year < FIRST_YEAR:
        return invalid(f"nobody was ringing changes in {year}")
    if not place.strip():
        return invalid("a report has to be about somewhere")
    if top < 1:
        return invalid("a leaderboard has to hold something")

    counted = statistics(performances, place=place)
    if not counted.ok:
        return Result(failure=counted.failure)
    totals = counted.unwrap()

    # Narrowed to the year here rather than in the query. The statistics
    # service does not filter by date and adding a parameter to it for one
    # caller would push a report's idea of a year down into everything.
    in_year = [view for view in performances.search(place=place) if view.rang_on.year == year]
    peals = sum(1 for view in in_year if view.length >= 5000)
    quarters = sum(1 for view in in_year if 1250 <= view.length < 5000)

    rang_on = {view.rang_on for view in in_year}
    marked = tuple(occasion.name for occasion in occasions(year) if occasion.when in rang_on)

    entered = []
    for stored in competitions.all():
        if stored.held_on.year != year:
            continue
        sheet = to_competition(stored)
        ours = sheet.find(place)
        entered.append(
            CompetitionLine(
                name=sheet.name,
                when=sheet.held_on,
                entered=ours is not None,
                position=None if ours is None else ours.position,
                bands=sheet.bands,
            )
        )

    covered = coverage(collections, ringers, against)
    band = ringers.all()

    return succeeded(
        AnnualView(
            year=year,
            place=place.strip(),
            totals=totals,
            peals=peals,
            quarters=quarters,
            other=len(in_year) - peals - quarters,
            changes=sum(view.length for view in in_year),
            ringers=len(band),
            top_ringers=_leaders(dict(totals.by_ringer), top),
            top_methods=_leaders(dict(totals.by_method), top),
            competitions=tuple(sorted(entered, key=lambda line: line.when)),
            repertoire=len({title for view in in_year for title in [view.title]}),
            covers=covered.unwrap().share if covered.ok else 0.0,
            occasions_rung=marked,
        )
    )
