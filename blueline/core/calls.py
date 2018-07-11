"""Bobs and singles, which is how a touch gets any length.

A plain course comes round on its own after a few leads, so on its own it is
not much of a performance. A call swaps one change near the end of a lead for a
different one, which sends the working bells round a different way and puts off
the moment rounds comes back.

A call is held as the change it puts in and how far from the end of the lead it
goes. Nearly always that is the lead end itself, but not always, and a type
that can only do lead ends would have to be thrown away the first time somebody
wanted to call a method where the bob comes earlier.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from dataclasses import dataclass

from blueline.core.notation import Change, parse_change
from blueline.core.row import Row
from blueline.core.stage import check_stage
from blueline.errors import CallError


@dataclass(frozen=True)
class Call:
    """One call, as the change it substitutes and where it goes."""

    name: str
    symbol: str
    change: Change
    #: How far back from the end of the lead the change is replaced, nought
    #: meaning the lead end change itself.
    offset: int = 0

    def __post_init__(self) -> None:
        if self.offset < 0:
            raise CallError(f"{self.name} cannot be called past the end of the lead")

    @property
    def stage(self) -> int:
        return self.change.stage

    def __str__(self) -> str:
        return self.symbol

    def index_in(self, lead_length: int) -> int:
        """Which change in the lead this call replaces."""
        index = lead_length - 1 - self.offset
        if index < 0:
            raise CallError(f"{self.name} does not fit in a lead of {lead_length}")
        return index


#: A plain lead, which is no call at all. Useful so a touch can be written as
#: a run of symbols with plains in it rather than as gaps.
PLAIN = "p"


def plain_bob_calls(stage: int) -> Dict[str, Call]:
    """The usual bob and single for a Plain Bob sort of method.

    The bob makes fourths where the plain lead makes seconds, and the single
    holds thirds as well so that two bells swap rather than three moving round.
    """
    check_stage(stage)
    if stage < 4:
        raise CallError(f"there is no room for a fourths place bob at stage {stage}")
    return {
        "-": Call("Bob", "-", parse_change("14", stage)),
        "s": Call("Single", "s", parse_change("1234", stage)),
    }


def grandsire_calls(stage: int) -> Dict[str, Call]:
    """The bob and single for Grandsire, which come a change earlier.

    Grandsire is called at the change before the lead end, which is why a bob
    is thirds rather than fourths and why the offset is one rather than nought.
    """
    check_stage(stage)
    if stage < 5:
        raise CallError(f"Grandsire needs at least five bells, not {stage}")
    return {
        "-": Call("Bob", "-", parse_change("3", stage), offset=1),
        "s": Call("Single", "s", parse_change("345", stage), offset=1),
    }


def apply_call(changes: Tuple[Change, ...], call: Optional[Call]) -> List[Change]:
    """The changes of one lead, with a call swapped in if there is one."""
    lead = list(changes)
    if call is None:
        return lead
    if call.stage != lead[0].stage:
        raise CallError(f"{call.name} is stage {call.stage}, the method is not")
    lead[call.index_in(len(lead))] = call.change
    return lead


def called_lead(changes: Tuple[Change, ...], call: Optional[Call], start: Row) -> List[Row]:
    """Ring one lead from a row, with a call if one was made."""
    rows = [start]
    row = start
    for change in apply_call(changes, call):
        row = change.apply(row)
        rows.append(row)
    return rows
