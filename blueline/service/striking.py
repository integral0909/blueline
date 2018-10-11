"""Judging striking, and saying who won.

The core counts faults in a run of blow times. What a competition needs on top
of that is a way to hand in several bands' attempts and get them back in order,
with the marking written the way a judge reads it out: the score, the worst
patch, and whether the band was drifting early or late.

Times come in as seconds from the start of the piece. Anything that records
striking gives them that way, and asking for gaps instead would mean every
caller doing the same subtraction first.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from dataclasses import dataclass

from blueline.core.striking import FAULT_THRESHOLD, Fault, Judgement, StrikingError, judge
from blueline.service.results import Result, invalid, succeeded

#: How many faults a judge would read out before saying "and so on". A whole
#: peal's worth listed in full is not a marking, it is a transcript.
WORST = 5


@dataclass(frozen=True)
class StrikingReport:
    """One band's attempt, marked."""

    band: str
    rows: int
    blows: int
    faults: int
    percentage: float
    spread: float
    drift: str
    worst: Tuple[str, ...]

    def summary(self) -> str:
        return f"{self.band}: {self.faults} faults, {self.percentage:.1f}% clean"


def drift_of(faults: Tuple[Fault, ...]) -> str:
    """Whether a band was mostly early, mostly late, or neither.

    A band that is consistently one way has a fixable problem: usually the
    whole ring is going faster or slower than the conductor thinks. A band
    scattered both ways has an unsteady one, which is a harder thing to tell
    somebody.
    """
    if not faults:
        return "even"
    early = sum(1 for fault in faults if fault.was_early)
    late = len(faults) - early
    if early > late * 2:
        return "early"
    if late > early * 2:
        return "late"
    return "unsteady"


def worst_of(judgement: Judgement, count: int = WORST) -> Tuple[str, ...]:
    """The faults a judge would actually mention, biggest first."""
    ordered = sorted(judgement.faults, key=lambda fault: abs(fault.error), reverse=True)
    return tuple(str(fault) for fault in ordered[:count])


def report_of(band: str, judgement: Judgement) -> StrikingReport:
    return StrikingReport(
        band=band,
        rows=judgement.rows,
        blows=judgement.blows,
        faults=judgement.fault_count,
        percentage=judgement.percentage,
        spread=judgement.spread,
        drift=drift_of(judgement.faults),
        worst=worst_of(judgement),
    )


def mark(
    band: str,
    times: List[float],
    stage: int,
    threshold: float = FAULT_THRESHOLD,
) -> Result[StrikingReport]:
    """Judge one attempt."""
    if not band.strip():
        return invalid("a band needs a name")
    if not 0 < threshold < 1:
        return invalid("a threshold is a share of a gap, so between 0 and 1")
    try:
        judgement = judge(times, stage, threshold=threshold)
    except StrikingError as error:
        return invalid(str(error))
    return succeeded(report_of(band.strip(), judgement))


def order_of_merit(
    attempts: Dict[str, List[float]],
    stage: int,
    threshold: float = FAULT_THRESHOLD,
) -> Result[List[StrikingReport]]:
    """Every band in a competition, best struck first.

    Ties are broken on spread, because two bands on the same fault count are
    separated by which of them was steadier, and that is what a judge would
    say when asked.
    """
    if not attempts:
        return invalid("no bands to judge")

    marked: List[StrikingReport] = []
    for band, times in attempts.items():
        result = mark(band, times, stage, threshold=threshold)
        if not result.ok:
            assert result.failure is not None
            return invalid(f"{band}: {result.failure.detail}")
        marked.append(result.unwrap())

    marked.sort(key=lambda report: (-report.percentage, report.spread, report.band))
    return succeeded(marked)
