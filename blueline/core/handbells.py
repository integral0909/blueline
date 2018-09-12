"""Ringing in hand, where one person has two bells.

A band of eight in a tower is eight people. The same peal in hand is four,
each ringing a pair, and which pair they have changes what they are doing
entirely: the two bells of a pair cross and dodge with each other, and a pair
that never meets is a different job from one that is always together.

Pairs are almost always adjacent and odd first, so 1-2, 3-4, 5-6, 7-8. That is
not a rule anybody could not break, but it is what nearly every handbell peal
does, and a library that could not say so would make the common case awkward.
"""

from __future__ import annotations

from typing import List, Set, Tuple

from dataclasses import dataclass

from blueline.core.method import Method
from blueline.core.row import Row
from blueline.core.stage import check_stage, is_odd_stage
from blueline.errors import BluelineError


class HandbellError(BluelineError):
    """A pairing that will not work."""


@dataclass(frozen=True)
class Pair:
    """Two bells rung by one person."""

    lower: int
    higher: int

    def __post_init__(self) -> None:
        if self.lower >= self.higher:
            raise HandbellError(f"{self.lower} and {self.higher} are not a pair")

    @property
    def bells(self) -> Tuple[int, int]:
        return (self.lower, self.higher)

    @property
    def is_adjacent(self) -> bool:
        return self.higher == self.lower + 1

    def __str__(self) -> str:
        return f"{self.lower}-{self.higher}"

    def __contains__(self, bell: int) -> bool:
        return bell in self.bells


def standard_pairs(stage: int) -> List[Pair]:
    """The usual pairing, which is adjacent bells from the treble up.

    An odd stage leaves the tenor covering on its own, which is what happens
    in practice: somebody rings it as a single with their other hand free.
    """
    check_stage(stage)
    working = stage - 1 if is_odd_stage(stage) else stage
    return [Pair(lower=bell, higher=bell + 1) for bell in range(1, working, 2)]


def pairs_from(pairing: List[Tuple[int, int]], stage: int) -> List[Pair]:
    """Build a pairing somebody has asked for, checking it hangs together."""
    check_stage(stage)
    made = [Pair(lower=min(pair), higher=max(pair)) for pair in pairing]
    seen: Set[int] = set()
    for pair in made:
        for bell in pair.bells:
            if bell < 1 or bell > stage:
                raise HandbellError(f"there is no bell {bell} at stage {stage}")
            if bell in seen:
                raise HandbellError(f"bell {bell} is in two pairs")
            seen.add(bell)
    return made


def unpaired(pairs: List[Pair], stage: int) -> List[int]:
    """Bells nobody has, which at an odd stage is the covering tenor."""
    taken = {bell for pair in pairs for bell in pair.bells}
    return [bell for bell in range(1, stage + 1) if bell not in taken]


def crossings(method: Method, pair: Pair) -> List[int]:
    """Where a pair's two bells cross over each other in a lead.

    Crossing is the thing a handbell ringer feels. The two bells swap which is
    above the other, and knowing where that happens is most of learning a
    method in hand.
    """
    rows = method.lead_rows()
    found: List[int] = []
    for index in range(len(rows) - 1):
        before = _above(rows[index], pair)
        after = _above(rows[index + 1], pair)
        if before != after:
            found.append(index + 1)
    return found


def _above(row: Row, pair: Pair) -> int:
    """Which of the pair is nearer the front in a row."""
    return pair.lower if row.place_of(pair.lower) < row.place_of(pair.higher) else pair.higher


def together(method: Method, pair: Pair) -> List[int]:
    """Rows where a pair's bells are struck next to each other."""
    rows = method.lead_rows()
    return [
        index
        for index, row in enumerate(rows)
        if abs(row.place_of(pair.lower) - row.place_of(pair.higher)) == 1
    ]
