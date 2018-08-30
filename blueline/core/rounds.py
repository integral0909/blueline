"""Coming round, and the things that stop a touch dead.

A touch ends when rounds comes up, whether or not that was the plan. A
composition that comes round at the third lead is not a short composition, it
is a broken one, and a conductor needs to know which lead it happens at rather
than being told the length is wrong.

There is a second way a touch can be spoiled that has nothing to do with truth:
coming round in the middle of a lead. Ringers stand at a lead end, so rounds
turning up halfway through means the band either carries on past it or stops
somewhere they cannot stop. Both are worth reporting.
"""

from __future__ import annotations

from typing import List, Optional

from dataclasses import dataclass

from blueline.core.row import Row


@dataclass(frozen=True)
class RoundsAt:
    """Somewhere rounds turned up."""

    row: int
    lead: int
    at_lead_end: bool

    def __str__(self) -> str:
        where = "at the lead end" if self.at_lead_end else "part way through the lead"
        return f"row {self.row}, lead {self.lead}, {where}"


def find_rounds(rows: List[Row], lead_length: int, skip_opening: bool = True) -> List[RoundsAt]:
    """Every place rounds comes up, with which lead it falls in.

    The opening row is rounds by definition and is skipped, because reporting
    it would bury the one occurrence anybody cares about.
    """
    if lead_length < 1:
        raise ValueError("a lead has to have at least one row in it")
    found: List[RoundsAt] = []
    for index, row in enumerate(rows):
        if index == 0 and skip_opening:
            continue
        if not row.is_rounds:
            continue
        found.append(
            RoundsAt(
                row=index,
                lead=(index - 1) // lead_length + 1,
                at_lead_end=index % lead_length == 0,
            )
        )
    return found


def comes_round_early(rows: List[Row], lead_length: int) -> Optional[RoundsAt]:
    """The first rounds before the end, or nothing if it runs to the finish."""
    found = find_rounds(rows[:-1], lead_length)
    return found[0] if found else None


def ends_at_a_lead_end(rows: List[Row], lead_length: int) -> bool:
    """Whether the touch finishes somewhere a band could actually stand."""
    if not rows:
        return False
    return (len(rows) - 1) % lead_length == 0


def rounds_in_the_middle(rows: List[Row], lead_length: int) -> List[RoundsAt]:
    """Rounds turning up part way through a lead, which cannot be stood at."""
    return [entry for entry in find_rounds(rows, lead_length) if not entry.at_lead_end]
