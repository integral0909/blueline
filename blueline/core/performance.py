"""A performance, which is a composition somebody actually rang.

Everything else in this library is about what could be rung. This is about what
was: a band, a method, a length, a place and a date. It is the thing that goes
on a peal board and into a report, and it is where the pieces stop being
abstract.

A performance is checked against itself rather than trusted. A band of eight
cannot ring minor, a peal has to be long enough to be one, and a length that
does not match the composition it claims to be is worth refusing before it gets
written on a wall in gold leaf.
"""

from __future__ import annotations

from typing import List, Optional

from dataclasses import dataclass
from datetime import date

from blueline.core.bands import Band
from blueline.core.peals import Standing, standing_of
from blueline.errors import BluelineError


class PerformanceError(BluelineError):
    """A performance that does not hang together."""


@dataclass(frozen=True)
class Performance:
    """What a band rang, where, and when."""

    band: Band
    title: str
    stage: int
    length: int
    rang_on: date
    place: str
    composer: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise PerformanceError("a performance has to say what was rung")
        if not self.place.strip():
            raise PerformanceError("a performance has to say where it was rung")
        if self.length < 1:
            raise PerformanceError(f"cannot ring {self.length} changes")
        if not self.band.rings(self.stage):
            raise PerformanceError(f"a band of {self.band.stage} cannot ring {self.stage} bells")

    @property
    def standing(self) -> Standing:
        return standing_of(self.length, self.stage)

    @property
    def is_peal(self) -> bool:
        return self.standing.is_peal

    @property
    def has_covering_tenor(self) -> bool:
        """Whether somebody rang a bell that took no part in the changes."""
        return self.band.stage > self.stage

    def headline(self) -> str:
        """The line at the top of a peal board."""
        return f"{self.place}, {self.rang_on:%d %B %Y}"

    def summary(self) -> str:
        counts = self.standing.counts_as
        return f"{self.length} {self.title}, a {counts} at {self.place}"

    def board(self) -> List[str]:
        """The whole thing as it would be written up."""
        lines = [self.headline(), "", f"{self.length} {self.title}"]
        if self.composer:
            lines.append(f"Composed by {self.composer}")
        lines.append("")
        lines.extend(self.band.lines())
        if self.has_covering_tenor:
            lines.append(f"{self.band.stage} covering")
        return lines
