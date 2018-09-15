"""Getting to a length, which is the composer's actual problem.

Nobody sets out to ring a touch of some length or other. They want a quarter,
or a peal, and the question is what calling gets there. That is a different
search from finding any true touch: the length is fixed first and everything
that cannot reach it is thrown away.

The trick is knowing when to stop. A block of leads that is already longer
than the target cannot be shortened by adding to it, so the branch goes. And a
block whose remaining length cannot be made up in whole leads will never land
on the number exactly, which rules out most of the tree before it is walked.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from dataclasses import dataclass

from blueline.core.calls import Call
from blueline.core.method import Method
from blueline.core.peals import peal_length, quarter_length
from blueline.core.search import Found, Limits, search_callings
from blueline.core.truth import extent_length


@dataclass(frozen=True)
class Target:
    """A length somebody is trying to reach, and how close is close enough."""

    length: int
    #: How far either side still counts. A quarter is usually rung to the
    #: exact number, but a band asking for about twelve hundred means it.
    tolerance: int = 0

    def __post_init__(self) -> None:
        if self.length < 1:
            raise ValueError(f"cannot aim for {self.length} changes")
        if self.tolerance < 0:
            raise ValueError("a tolerance cannot be negative")

    @property
    def shortest(self) -> int:
        return max(1, self.length - self.tolerance)

    @property
    def longest(self) -> int:
        return self.length + self.tolerance

    def accepts(self, length: int) -> bool:
        return self.shortest <= length <= self.longest

    def __str__(self) -> str:
        if not self.tolerance:
            return str(self.length)
        return f"{self.length} give or take {self.tolerance}"


def quarter_target(stage: int, tolerance: int = 0) -> Target:
    return Target(length=quarter_length(stage), tolerance=tolerance)


def peal_target(stage: int, tolerance: int = 0) -> Target:
    return Target(length=peal_length(stage), tolerance=tolerance)


def reachable(method: Method, target: Target) -> bool:
    """Whether the target can be hit at all with whole leads of this method.

    Two things rule a target out before any searching. No true touch can be
    longer than the extent, because past that there are no rows left to ring:
    a true twelve hundred and sixty of minor does not exist and looking for
    one takes seven seconds to find that out. And a length that is not a
    multiple of the lead length cannot be reached however the calls fall.
    """
    if target.shortest > extent_length(method.stage):
        return False
    lead = method.lead_length
    return any(length % lead == 0 for length in range(target.shortest, target.longest + 1))


def leads_needed(method: Method, target: Target) -> Tuple[int, int]:
    """The fewest and most leads that could land inside the target."""
    lead = method.lead_length
    return (target.shortest + lead - 1) // lead, target.longest // lead


def find_for(
    method: Method,
    calls: Dict[str, Call],
    target: Target,
    max_found: int = 10,
    allowed: Optional[str] = None,
) -> Tuple[List[Found], bool]:
    """Callings that come round true at the target length.

    Gives back what was found and whether the search finished, the same as the
    general one. A search that stopped at a cap has proved nothing about what
    it did not look at.
    """
    if not reachable(method, target):
        return [], True

    fewest, most = leads_needed(method, target)
    limits = Limits(
        min_length=target.shortest,
        max_length=target.longest,
        max_leads=max(1, most),
        max_found=max_found,
    )
    found, exhausted = search_callings(method, calls, limits, allowed=allowed)
    return [entry for entry in found if entry.leads >= fewest], exhausted
