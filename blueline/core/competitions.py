"""A striking competition, as a thing rather than as rows in a table.

The service marks blow times and the database keeps sheets. In between there
has to be something that knows what a competition is: several bands who all
rang the same thing, put in an order somebody announced.

Nothing here talks to a database and nothing here judges any striking. It holds
what a sheet says and answers the questions somebody asks of a sheet: who won,
who has improved, and whether the order makes sense at all.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from dataclasses import dataclass, field
from datetime import date

from blueline.errors import BluelineError


class CompetitionError(BluelineError):
    """A competition sheet that does not make sense."""


@dataclass(frozen=True)
class Entry:
    """One band's result."""

    band: str
    position: int
    faults: int
    percentage: float
    drift: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if not self.band.strip():
            raise CompetitionError("a band needs a name")
        if self.position < 1:
            raise CompetitionError(f"{self.band}: a position starts at one")
        if self.faults < 0:
            raise CompetitionError(f"{self.band}: faults cannot be negative")

    def __str__(self) -> str:
        return f"{self.position}. {self.band}, {self.faults} faults"


@dataclass(frozen=True)
class Competition:
    """A sheet: who rang, on what, and in what order they came."""

    name: str
    held_on: date
    stage: int
    entries: Tuple[Entry, ...] = field(default_factory=tuple)
    place: str = ""
    judge: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise CompetitionError("a competition needs a name")
        if self.stage < 1:
            raise CompetitionError("a competition needs bells")
        bands = [entry.band.strip().lower() for entry in self.entries]
        if len(set(bands)) != len(bands):
            raise CompetitionError("a band cannot enter twice")

    @property
    def bands(self) -> int:
        return len(self.entries)

    def ordered(self) -> Tuple[Entry, ...]:
        """The entries as they were read out, best first.

        Sorted by position and then by name, because two bands placed equal
        have to come out in some order and alphabetical is the one nobody
        reads anything into.
        """
        return tuple(sorted(self.entries, key=lambda entry: (entry.position, entry.band)))

    def winner(self) -> Optional[Entry]:
        """Whoever was placed first, or nobody if two were."""
        first = [entry for entry in self.entries if entry.position == 1]
        return first[0] if len(first) == 1 else None

    def find(self, band: str) -> Optional[Entry]:
        wanted = band.strip().lower()
        for entry in self.entries:
            if entry.band.strip().lower() == wanted:
                return entry
        return None

    def summary(self) -> str:
        if not self.entries:
            return f"{self.name}, {self.held_on:%Y-%m-%d}, nobody entered"
        winner = self.winner()
        who = winner.band if winner is not None else "a tie"
        return f"{self.name}, {self.held_on:%Y-%m-%d}, {self.bands} bands, won by {who}"


def placings(competition: Competition, band: str) -> Optional[int]:
    """Where a band came, or nothing if they did not enter."""
    entry = competition.find(band)
    return None if entry is None else entry.position


def progress(sheets: List[Competition], band: str) -> List[Tuple[date, int]]:
    """Where a band came each year they entered, oldest first.

    A band that missed a year is simply absent rather than carried forward.
    Drawing a line through a gap would say they were somewhere they were not.
    """
    found: List[Tuple[date, int]] = []
    for sheet in sorted(sheets, key=lambda sheet: sheet.held_on):
        place = placings(sheet, band)
        if place is not None:
            found.append((sheet.held_on, place))
    return found


def improving(sheets: List[Competition], band: str) -> Optional[bool]:
    """Whether a band is doing better than it was.

    Two entries is the least that can say anything. Compared on the first and
    the last rather than on every step, because a band that slipped one year
    and recovered has still improved and a rule that looked at each pair in
    turn would say otherwise.
    """
    seen = progress(sheets, band)
    if len(seen) < 2:
        return None
    return seen[-1][1] < seen[0][1]
