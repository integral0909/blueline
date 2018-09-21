"""Lead head groups, which is how composers file methods.

Two methods with the same lead heads take the same compositions. That is the
whole reason the groups exist: a composer who has written a peal of Cambridge
can ring it to Yorkshire without touching a calling, because the bells are in
the same places at every lead end.

The groups are named by a letter. Which letter a method gets depends on the
order its lead heads come round in, and that falls out of the lead head itself,
so it can be worked out rather than looked up. The names here follow the usual
lettering for methods with the treble as the only hunt bell.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from dataclasses import dataclass

from blueline.core.method import Method
from blueline.core.row import Row


@dataclass(frozen=True)
class LeadHeadGroup:
    """A lead head, and the course of heads it generates."""

    head: Row
    order: int
    heads: Tuple[Row, ...]
    places_at_lead_end: str

    def __str__(self) -> str:
        return f"{self.head} ({self.places_at_lead_end}, {self.order} leads)"


def heads_of(method: Method) -> Tuple[Row, ...]:
    """Every lead head of the plain course, in the order they come round."""
    heads: List[Row] = []
    row = Row.rounds(method.stage)
    for _ in range(method.leads_in_course):
        row = row.transposed_by(method.lead_head)
        heads.append(row)
    return tuple(heads)


def group_of(method: Method) -> LeadHeadGroup:
    """The lead head group a method belongs to."""
    return LeadHeadGroup(
        head=method.lead_head,
        order=method.leads_in_course,
        heads=heads_of(method),
        places_at_lead_end=str(method.changes[-1]),
    )


def share_lead_heads(first: Method, second: Method) -> bool:
    """Whether two methods take each other's compositions.

    The lead head itself has to match, not just the set of rows the course
    passes through. Comparing sets looked more generous and was wrong: at
    major every one of these methods runs through the same seven rows with the
    treble leading, so set equality put Bristol in with Cambridge when their
    lead ends are eighths and seconds and no calling moves between them.

    This is the same test splicing uses, which is the point: methods that
    share a lead head can be spliced and can share a composition.
    """
    if first.stage != second.stage:
        return False
    return first.lead_head == second.lead_head


def group_methods(methods: List[Method]) -> Dict[str, List[str]]:
    """Sort methods into the groups that take the same compositions.

    Keyed on the lead head, which is what share_lead_heads compares and what
    splicing needs. Names within a group come back sorted so the listing is
    settled between runs.
    """
    grouped: Dict[str, List[str]] = {}
    for method in methods:
        key = str(method.lead_head)
        grouped.setdefault(key, []).append(f"{method.name} {method.stage}")
    return {key: sorted(names) for key, names in sorted(grouped.items())}
