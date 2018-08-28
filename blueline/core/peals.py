"""Peals and quarter peals, which is what a band is actually trying to ring.

A touch is any length. A performance has to reach a length that counts, and
what counts is fixed by the stage: five thousand changes on eight bells or
fewer, five thousand and forty on seven, and a quarter is a quarter of that
rounded the way ringers round it.

The rules are not arbitrary. An extent of seven bells is 5040, so a peal on
seven is exactly one extent and a peal on eight has to be at least 5000 without
any such natural length to sit on. Getting the boundary wrong means telling a
band their peal did not count, so the numbers are written down rather than
worked out on the fly.
"""

from __future__ import annotations

from typing import Dict, Tuple

from dataclasses import dataclass

from blueline.core.stage import check_stage

#: The shortest length that counts as a peal, by stage.
PEAL_LENGTHS: Dict[int, int] = {
    3: 5040,
    4: 5040,
    5: 5040,
    6: 5040,
    7: 5040,
    8: 5000,
    9: 5000,
    10: 5000,
    11: 5000,
    12: 5000,
    13: 5000,
    14: 5000,
    15: 5000,
    16: 5000,
}

#: What a band calls a length that is neither a peal nor a quarter.
TOUCH = "touch"
QUARTER = "quarter peal"
PEAL = "peal"


@dataclass(frozen=True)
class Standing:
    """What a length counts as, and how far off the next thing it is."""

    length: int
    counts_as: str
    short_by: int

    @property
    def is_peal(self) -> bool:
        return self.counts_as == PEAL

    @property
    def is_quarter(self) -> bool:
        return self.counts_as == QUARTER

    def __str__(self) -> str:
        if self.short_by:
            return f"{self.length} changes, {self.short_by} short of a {_next_up(self.counts_as)}"
        return f"{self.length} changes, a {self.counts_as}"


def peal_length(stage: int) -> int:
    """The shortest length that counts as a peal at a stage."""
    check_stage(stage)
    return PEAL_LENGTHS[stage]


def quarter_length(stage: int) -> int:
    """A quarter of a peal, rounded up the way ringers round it.

    A quarter of 5040 is 1260 exactly. A quarter of 5000 is 1250. Both are the
    figures used, so no rounding rule has to be invented.
    """
    return peal_length(stage) // 4


def _next_up(counts_as: str) -> str:
    return {TOUCH: QUARTER, QUARTER: PEAL}.get(counts_as, PEAL)


def standing_of(length: int, stage: int) -> Standing:
    """What a length counts as, and what it would take to be the next thing."""
    peal = peal_length(stage)
    quarter = quarter_length(stage)
    if length >= peal:
        return Standing(length=length, counts_as=PEAL, short_by=0)
    if length >= quarter:
        return Standing(length=length, counts_as=QUARTER, short_by=peal - length)
    return Standing(length=length, counts_as=TOUCH, short_by=quarter - length)


def is_peal(length: int, stage: int) -> bool:
    return length >= peal_length(stage)


def is_quarter(length: int, stage: int) -> bool:
    return quarter_length(stage) <= length < peal_length(stage)


def extents_in(length: int, stage: int) -> Tuple[int, int]:
    """How many whole extents a length is, and how much is left over.

    A peal of minor is seven extents of 720 exactly, which is why minor peals
    are rung that way and why a length that does not divide is worth knowing
    about before anybody starts.
    """
    from blueline.core.truth import extent_length

    size = extent_length(stage)
    return divmod(length, size)
