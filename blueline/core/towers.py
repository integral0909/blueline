"""Towers, and what they are able to ring.

A tower has a number of bells and a weight, and both decide what can happen in
it. Six bells means minor and nothing above it. A heavy ring means a slower
peal and a band that can handle it, and ringers care enough about tenor weight
that it goes on every peal report next to the tower's name.

Weights are in hundredweight, quarters and pounds, which is how every ring in
the country is described and how every ringer talks about them. A tower of
twenty three hundredweight is a different proposition from one of eight, and
converting both to kilograms would lose the thing people actually recognise.
"""

from __future__ import annotations

from dataclasses import dataclass

from blueline.core.stage import check_stage
from blueline.errors import BluelineError

POUNDS_PER_QUARTER = 28
QUARTERS_PER_HUNDREDWEIGHT = 4
POUNDS_PER_HUNDREDWEIGHT = POUNDS_PER_QUARTER * QUARTERS_PER_HUNDREDWEIGHT
KILOGRAMS_PER_POUND = 0.45359237


class TowerError(BluelineError):
    """A tower that could not be described."""


@dataclass(frozen=True)
class Weight:
    """A bell's weight, in hundredweight, quarters and pounds."""

    hundredweight: int
    quarters: int = 0
    pounds: int = 0

    def __post_init__(self) -> None:
        if self.hundredweight < 0 or self.quarters < 0 or self.pounds < 0:
            raise TowerError("a bell cannot weigh less than nothing")
        if self.quarters >= QUARTERS_PER_HUNDREDWEIGHT:
            raise TowerError(f"{self.quarters} quarters is more than a hundredweight")
        if self.pounds >= POUNDS_PER_QUARTER:
            raise TowerError(f"{self.pounds} pounds is more than a quarter")

    @property
    def total_pounds(self) -> int:
        return (
            self.hundredweight * POUNDS_PER_HUNDREDWEIGHT
            + self.quarters * POUNDS_PER_QUARTER
            + self.pounds
        )

    @property
    def kilograms(self) -> float:
        return self.total_pounds * KILOGRAMS_PER_POUND

    def __str__(self) -> str:
        """The way it is written on a peal board, such as 23-1-14."""
        return f"{self.hundredweight}-{self.quarters}-{self.pounds}"

    def __lt__(self, other: Weight) -> bool:
        return self.total_pounds < other.total_pounds


def weight_from_pounds(pounds: int) -> Weight:
    """Build a weight from a total, which is how a spreadsheet stores one."""
    if pounds < 0:
        raise TowerError("a bell cannot weigh less than nothing")
    hundredweight, rest = divmod(pounds, POUNDS_PER_HUNDREDWEIGHT)
    quarters, remainder = divmod(rest, POUNDS_PER_QUARTER)
    return Weight(hundredweight=hundredweight, quarters=quarters, pounds=remainder)


def parse_weight(text: str) -> Weight:
    """Read a weight written the way ringers write it, such as 23-1-14."""
    parts = [part.strip() for part in text.strip().split("-")]
    if not 1 <= len(parts) <= 3:
        raise TowerError(f"{text!r} is not a weight, want something like 23-1-14")
    try:
        numbers = [int(part) for part in parts]
    except ValueError as error:
        raise TowerError(f"{text!r} is not a weight") from error
    while len(numbers) < 3:
        numbers.append(0)
    return Weight(hundredweight=numbers[0], quarters=numbers[1], pounds=numbers[2])


@dataclass(frozen=True)
class Tower:
    """A ring of bells somewhere."""

    place: str
    bells: int
    tenor: Weight

    def __post_init__(self) -> None:
        if not self.place.strip():
            raise TowerError("a tower has to be somewhere")
        check_stage(self.bells)

    def rings(self, stage: int) -> bool:
        """Whether a method at this stage can be rung here.

        A ring of eight can ring triples with the tenor covering, and anything
        smaller than that outright, so the only thing ruled out is a stage
        bigger than the ring.
        """
        return 3 <= stage <= self.bells

    @property
    def is_heavy(self) -> bool:
        """Whether the tenor is heavy enough to be worth remarking on."""
        return self.tenor.hundredweight >= 20

    def __str__(self) -> str:
        return f"{self.place}, {self.bells} bells, tenor {self.tenor}"
