"""Recording what happened at a striking competition.

Two ways in, because there are two ways it actually happens. Either somebody
recorded the striking and the marking falls out of the blow times, or the judge
announced an order on the day and all anybody has afterwards is the sheet. The
second is far more common and refusing it would mean refusing every competition
held before anybody brought a microphone.

Where blow times are given, the position comes from the marking. Where they are
not, the caller says what was announced, and nothing here second guesses it: a
judge can move a band down for a mistake the fault count knows nothing about.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from dataclasses import dataclass
from datetime import date

from blueline.core.competitions import (
    Competition,
    CompetitionError,
    Entry,
    improving,
    progress,
)
from blueline.db.repository import CompetitionRepository, to_competition
from blueline.errors import LibraryError
from blueline.service.results import Result, already_exists, invalid, not_found, succeeded
from blueline.service.striking import order_of_merit


@dataclass(frozen=True)
class CompetitionView:
    """A sheet as anything outside the service sees it."""

    id: int
    name: str
    held_on: date
    place: str
    judge: str
    stage: int
    bands: int
    winner: str
    entries: Tuple[Entry, ...]

    def summary(self) -> str:
        return f"{self.name}, {self.held_on:%Y-%m-%d}, {self.bands} bands"


@dataclass(frozen=True)
class ProgressView:
    """How a band has done over the years."""

    band: str
    placings: Tuple[Tuple[date, int], ...]
    improving: Optional[bool]

    @property
    def entered(self) -> int:
        return len(self.placings)

    @property
    def best(self) -> Optional[int]:
        return min((place for _, place in self.placings), default=None)

    def summary(self) -> str:
        if not self.placings:
            return f"{self.band} has not entered"
        way = {True: "improving", False: "slipping", None: "too few to say"}[self.improving]
        return f"{self.band}, {self.entered} entries, best {self.best}, {way}"


def view_of(stored_id: int, sheet: Competition) -> CompetitionView:
    winner = sheet.winner()
    return CompetitionView(
        id=stored_id,
        name=sheet.name,
        held_on=sheet.held_on,
        place=sheet.place,
        judge=sheet.judge,
        stage=sheet.stage,
        bands=sheet.bands,
        winner=winner.band if winner is not None else "",
        entries=sheet.ordered(),
    )


def entries_from_times(
    attempts: Dict[str, List[float]],
    stage: int,
) -> Result[Tuple[Entry, ...]]:
    """Mark every band and place them by what the marking came to."""
    marked = order_of_merit(attempts, stage)
    if not marked.ok:
        return invalid(str(marked.failure))
    return succeeded(
        tuple(
            Entry(
                band=report.band,
                position=position,
                faults=report.faults,
                percentage=round(report.percentage, 2),
                drift=report.drift,
            )
            for position, report in enumerate(marked.unwrap(), start=1)
        )
    )


def record(
    repository: CompetitionRepository,
    name: str,
    held_on: date,
    stage: int,
    entries: Tuple[Entry, ...],
    place: str = "",
    judge: str = "",
) -> Result[CompetitionView]:
    """Put a sheet in."""
    try:
        sheet = Competition(
            name=name,
            held_on=held_on,
            stage=stage,
            entries=entries,
            place=place,
            judge=judge,
        )
    except CompetitionError as error:
        return invalid(str(error))

    try:
        stored = repository.add(sheet)
    except LibraryError as error:
        return already_exists(str(error))
    return succeeded(view_of(stored.id, sheet))


def judge_and_record(
    repository: CompetitionRepository,
    name: str,
    held_on: date,
    stage: int,
    attempts: Dict[str, List[float]],
    place: str = "",
    judge: str = "",
) -> Result[CompetitionView]:
    """Mark the striking, then put the sheet in."""
    marked = entries_from_times(attempts, stage)
    if not marked.ok:
        return invalid(str(marked.failure))
    return record(
        repository,
        name=name,
        held_on=held_on,
        stage=stage,
        entries=marked.unwrap(),
        place=place,
        judge=judge,
    )


def fetch(repository: CompetitionRepository, competition_id: int) -> Result[CompetitionView]:
    try:
        stored = repository.get(competition_id)
    except LibraryError as error:
        return not_found(str(error))
    return succeeded(view_of(stored.id, to_competition(stored)))


def listing(
    repository: CompetitionRepository,
    name: Optional[str] = None,
    place: Optional[str] = None,
    band: Optional[str] = None,
    stage: Optional[int] = None,
) -> Result[List[CompetitionView]]:
    found = repository.search(name=name, place=place, band=band, stage=stage)
    return succeeded([view_of(stored.id, to_competition(stored)) for stored in found])


def remove(repository: CompetitionRepository, competition_id: int) -> Result[int]:
    try:
        repository.remove(competition_id)
    except LibraryError as error:
        return not_found(str(error))
    return succeeded(competition_id)


def band_progress(repository: CompetitionRepository, band: str) -> Result[ProgressView]:
    """Where a band has come each year it entered."""
    if not band.strip():
        return invalid("a band needs a name")
    sheets = repository.for_band(band)
    return succeeded(
        ProgressView(
            band=band.strip(),
            placings=tuple(progress(sheets, band)),
            improving=improving(sheets, band),
        )
    )
