"""How well a band struck, which is what a judge listens for.

Truth is a property of the composition. Striking is a property of the
performance: whether the bells fell evenly, whether anybody was consistently
early, whether it got worse as the band tired. A peal can be perfectly true and
badly struck, and at a striking competition the truth is assumed and the
striking is the whole marking.

What a judge counts is faults. A bell struck noticeably away from where it
should have been is one fault, and the score is the count against the number of
rows. Nothing here listens to anything; it takes the times somebody recorded
and works out what they add up to.
"""

from __future__ import annotations

from typing import List, Tuple

from dataclasses import dataclass
from statistics import mean, pstdev

from blueline.errors import BluelineError


class StrikingError(BluelineError):
    """Striking data that cannot be judged."""


#: How far off a blow has to be before a judge would count it, as a share of
#: the gap between blows. A tenth is about the point a listener notices.
FAULT_THRESHOLD = 0.10


@dataclass(frozen=True)
class Fault:
    """One blow struck away from where it belonged."""

    row: int
    place: int
    error: float

    @property
    def was_early(self) -> bool:
        return self.error < 0

    def __str__(self) -> str:
        way = "early" if self.was_early else "late"
        return f"row {self.row}, place {self.place}, {abs(self.error):.0%} {way}"


@dataclass(frozen=True)
class Judgement:
    """What a run of striking came to."""

    rows: int
    blows: int
    faults: Tuple[Fault, ...]
    spread: float

    @property
    def fault_count(self) -> int:
        return len(self.faults)

    @property
    def per_row(self) -> float:
        return self.fault_count / self.rows if self.rows else 0.0

    @property
    def percentage(self) -> float:
        """The share of blows struck well, which is how a score is quoted."""
        if not self.blows:
            return 100.0
        return 100.0 * (1 - self.fault_count / self.blows)

    def summary(self) -> str:
        return f"{self.fault_count} faults in {self.rows} rows, " f"{self.percentage:.1f}% clean"


def gaps_between(times: List[float]) -> List[float]:
    """The interval between one blow and the next."""
    if len(times) < 2:
        return []
    return [later - earlier for earlier, later in zip(times, times[1:])]


def judge(times: List[float], stage: int, threshold: float = FAULT_THRESHOLD) -> Judgement:
    """Count the faults in a run of blow times.

    The ideal gap is the average one, not a figure decided in advance. A band
    ringing steadily at a slower speed is not badly struck, and judging them
    against somebody else's rhythm would say they were.
    """
    if stage < 1:
        raise StrikingError("striking needs at least one bell")
    if len(times) < 2:
        raise StrikingError("striking needs at least two blows to compare")

    gaps = gaps_between(times)
    ideal = mean(gaps)
    if ideal <= 0:
        raise StrikingError("blows have to be struck in order")

    faults: List[Fault] = []
    for index, gap in enumerate(gaps):
        error = (gap - ideal) / ideal
        if abs(error) >= threshold:
            blow = index + 1
            faults.append(Fault(row=blow // stage + 1, place=blow % stage + 1, error=error))

    return Judgement(
        rows=max(1, len(times) // stage),
        blows=len(times),
        faults=tuple(faults),
        spread=pstdev(gaps) / ideal if len(gaps) > 1 else 0.0,
    )


def compare(first: Judgement, second: Judgement) -> str:
    """Which of two performances was better struck, in words."""
    if first.percentage > second.percentage:
        return "the first"
    if second.percentage > first.percentage:
        return "the second"
    return "much the same"
