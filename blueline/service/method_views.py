"""The shapes the method service hands back.

Kept apart from the operations so the operations stay about what to do and
these stay about what comes back. The api converters and the command line
renderers both import these and neither wants the service functions, which is
what made the split worth doing.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from dataclasses import dataclass


@dataclass(frozen=True)
class ImportReport:
    """What came of reading a file into the library."""

    added: Tuple[str, ...]
    skipped: Tuple[str, ...]
    problems: Tuple[str, ...]

    @property
    def total(self) -> int:
        return len(self.added) + len(self.skipped)

    def summary(self) -> str:
        parts = [f"{len(self.added)} added"]
        if self.skipped:
            parts.append(f"{len(self.skipped)} already there")
        if self.problems:
            parts.append(f"{len(self.problems)} could not be read")
        return ", ".join(parts)


@dataclass(frozen=True)
class LineView:
    """A bell's work through a lead, in the forms anybody wants it.

    The places and the description are for reading, the grid is for looking at,
    and the work is what a ringer actually memorises: where they lead, lie,
    dodge and make places.
    """

    bell: int
    places: Tuple[int, ...]
    described: str
    grid: Tuple[str, ...]
    work: Dict[str, List[int]]


@dataclass(frozen=True)
class HandbellView:
    """What one pair does through a lead."""

    pair: str
    bells: Tuple[int, int]
    crossings: Tuple[int, ...]
    together: Tuple[int, ...]

    def summary(self) -> str:
        crossed = len(self.crossings)
        word = "crossing" if crossed == 1 else "crossings"
        return f"{self.pair}: {crossed} {word}, together {len(self.together)} times"
