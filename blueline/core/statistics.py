"""Totals over a lot of performances.

A list of what a band has rung is not the same as knowing what they ring. The
questions people actually ask are how many peals, at how many towers, which
method most often, and who has rung the most, and every one of those is a
count over the whole list rather than a property of any single performance.

Nothing here touches a database. It takes performances and gives back totals,
so the same code answers the question whether the performances came from a
query, a file, or a test.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from collections import Counter
from dataclasses import dataclass, field
from datetime import date

from blueline.core.performance import Performance


@dataclass(frozen=True)
class Totals:
    """What a run of performances adds up to."""

    performances: int
    peals: int
    quarters: int
    changes: int
    places: int
    ringers: int
    first: Optional[date]
    last: Optional[date]
    by_method: Counter[str] = field(default_factory=Counter)
    by_place: Counter[str] = field(default_factory=Counter)
    by_ringer: Counter[str] = field(default_factory=Counter)
    by_stage: Counter[int] = field(default_factory=Counter)

    @property
    def touches(self) -> int:
        """Everything that was neither a peal nor a quarter."""
        return self.performances - self.peals - self.quarters

    @property
    def average_length(self) -> int:
        if not self.performances:
            return 0
        return self.changes // self.performances

    def most_rung_method(self) -> Optional[Tuple[str, int]]:
        return _top(self.by_method)

    def busiest_place(self) -> Optional[Tuple[str, int]]:
        return _top(self.by_place)

    def busiest_ringer(self) -> Optional[Tuple[str, int]]:
        return _top(self.by_ringer)

    def summary(self) -> str:
        if not self.performances:
            return "nothing rung"
        parts = [f"{self.performances} performances", f"{self.changes} changes"]
        if self.peals:
            parts.append(f"{self.peals} peals")
        if self.quarters:
            parts.append(f"{self.quarters} quarters")
        return ", ".join(parts)


def _top(counted: Counter[str]) -> Optional[Tuple[str, int]]:
    """The commonest entry, breaking ties by name so it is settled.

    most_common on its own returns whichever the dictionary happened to see
    first, which makes a report that changes between runs for no reason.
    """
    if not counted:
        return None
    best = max(counted.values())
    name = min(name for name, count in counted.items() if count == best)
    return name, best


def totals_of(performances: List[Performance]) -> Totals:
    """Add a run of performances up."""
    by_method: Counter[str] = Counter()
    by_place: Counter[str] = Counter()
    by_ringer: Counter[str] = Counter()
    by_stage: Counter[int] = Counter()
    peals = quarters = changes = 0
    dates: List[date] = []

    for performance in performances:
        by_method[performance.title] += 1
        by_place[performance.place] += 1
        by_stage[performance.stage] += 1
        for ringer in performance.band.ringers:
            by_ringer[ringer.strip()] += 1
        changes += performance.length
        dates.append(performance.rang_on)
        standing = performance.standing
        if standing.is_peal:
            peals += 1
        elif standing.is_quarter:
            quarters += 1

    return Totals(
        performances=len(performances),
        peals=peals,
        quarters=quarters,
        changes=changes,
        places=len(by_place),
        ringers=len(by_ringer),
        first=min(dates) if dates else None,
        last=max(dates) if dates else None,
        by_method=by_method,
        by_place=by_place,
        by_ringer=by_ringer,
        by_stage=by_stage,
    )


def leaderboard(counted: Counter[str], top: int = 10) -> List[Tuple[str, int]]:
    """The commonest entries, most first and then alphabetically.

    Sorted properly rather than by most_common, so two people on the same
    number come out in the same order every time.
    """
    return sorted(counted.items(), key=lambda pair: (-pair[1], pair[0]))[:top]
