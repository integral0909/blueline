"""Proving, which is checking no row gets rung twice.

This is the one thing a composition absolutely has to be. A touch that repeats
a row is false and will not be counted however good it sounds, so proving is
the first thing anybody does to a new composition and the last thing they do
before ringing it.

The naive way is to put every row in a set and see if the set is smaller than
the list. That answers yes or no and nothing else, which is no use to somebody
trying to fix a composition. What they want to know is which rows came round
twice and where, so the report carries that.

Rounds is a special case. Every touch opens and closes on it and that is not
falseness, so the closing row is left out before anything is counted.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from collections import defaultdict
from dataclasses import dataclass

from blueline.core.row import Row
from blueline.core.touch import Touch


@dataclass(frozen=True)
class Repeat:
    """A row that came up more than once, and where."""

    row: Row
    positions: Tuple[int, ...]

    @property
    def times(self) -> int:
        return len(self.positions)

    def __str__(self) -> str:
        places = ", ".join(str(position) for position in self.positions)
        return f"{self.row} at {places}"


@dataclass(frozen=True)
class TruthReport:
    """What proving a run of rows turned up."""

    total: int
    distinct: int
    repeats: Tuple[Repeat, ...]

    @property
    def is_true(self) -> bool:
        return not self.repeats

    @property
    def rows_repeated(self) -> int:
        return len(self.repeats)

    @property
    def worst(self) -> Optional[Repeat]:
        """The row rung most often, which is where to start looking."""
        if not self.repeats:
            return None
        return max(self.repeats, key=lambda repeat: repeat.times)

    def summary(self) -> str:
        if self.is_true:
            return f"true, {self.total} rows"
        return f"false, {self.rows_repeated} rows repeated out of {self.total}"


def prove(rows: List[Row]) -> TruthReport:
    """Check a run of rows for repeats, counting positions from one."""
    seen: Dict[Row, List[int]] = defaultdict(list)
    for position, row in enumerate(rows, start=1):
        seen[row].append(position)
    repeats = tuple(
        Repeat(row=row, positions=tuple(positions))
        for row, positions in seen.items()
        if len(positions) > 1
    )
    ordered = tuple(sorted(repeats, key=lambda repeat: repeat.positions[0]))
    return TruthReport(total=len(rows), distinct=len(seen), repeats=ordered)


def rung_rows(touch: Touch) -> List[Row]:
    """The rows a touch rings, without the closing rounds.

    Opening and closing on the same row is what coming round means, not a
    repeat, so counting it would call every true touch false.
    """
    return touch.rows()[:-1]


def prove_touch(touch: Touch) -> TruthReport:
    return prove(rung_rows(touch))


def rounds_at(rows: List[Row]) -> Tuple[int, ...]:
    """Where rounds comes up, so a touch that comes round early is spotted."""
    return tuple(position for position, row in enumerate(rows, start=1) if row.is_rounds)


def comes_round_early(touch: Touch) -> bool:
    """Whether rounds turns up before the end, which stops the touch there."""
    return bool(rounds_at(rung_rows(touch)[1:]))


def extent_length(stage: int) -> int:
    """How many rows there are in an extent, which is every row once."""
    total = 1
    for bell in range(2, stage + 1):
        total *= bell
    return total


def is_extent(touch: Touch) -> bool:
    """Whether a touch rings every row at its stage exactly once."""
    if not touch.comes_round():
        return False
    if not prove_touch(touch).is_true:
        return False
    return touch.length == extent_length(touch.stage)


def prove_against(rows: List[Row], already: List[Row]) -> TruthReport:
    """Prove a block against rows that have already been rung.

    A composition in parts is proved a part at a time against everything
    before it, which is much quicker than expanding the whole thing when the
    part is going to turn out false anyway.
    """
    return prove(already + rows)
