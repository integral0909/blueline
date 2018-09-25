"""Splicing, which is changing method partway through a touch.

A band that can ring six Surprise Major methods does not ring six separate
touches. They ring one, changing method at a lead end, and the interest is in
which method comes next and whether the whole thing stays true. A composition
like that is a run of leads each naming its own method rather than one method
and a calling.

The rule that makes it work is that methods can only be spliced where they
agree at the lead end. Two methods with different lead heads leave the bells in
different places, so a band ringing one and then the other would find the line
they had learnt no longer fits.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from dataclasses import dataclass

from blueline.core.calls import Call, called_lead
from blueline.core.leadheads import share_lead_heads
from blueline.core.method import Method
from blueline.core.row import Row
from blueline.errors import TouchError


@dataclass(frozen=True)
class Leg:
    """One lead of a spliced touch: which method, and what was called."""

    method: Method
    call: Optional[Call] = None

    @property
    def symbol(self) -> str:
        return "p" if self.call is None else self.call.symbol


@dataclass(frozen=True)
class Spliced:
    """A touch that changes method as it goes."""

    legs: Tuple[Leg, ...]

    def __post_init__(self) -> None:
        if not self.legs:
            raise TouchError("a spliced touch has to have at least one lead")
        stages = {leg.method.stage for leg in self.legs}
        if len(stages) > 1:
            raise TouchError(f"cannot splice across stages {sorted(stages)}")

    @property
    def stage(self) -> int:
        return self.legs[0].method.stage

    @property
    def leads(self) -> int:
        return len(self.legs)

    @property
    def length(self) -> int:
        return sum(leg.method.lead_length for leg in self.legs)

    @property
    def order(self) -> str:
        """The methods in order, by their initials, the way bands write it."""
        return "".join(leg.method.name[0].upper() for leg in self.legs)

    @property
    def calling(self) -> str:
        return "".join(leg.symbol for leg in self.legs)

    def methods_used(self) -> List[str]:
        seen: List[str] = []
        for leg in self.legs:
            if leg.method.name not in seen:
                seen.append(leg.method.name)
        return sorted(seen)

    def rows(self, start: Optional[Row] = None) -> List[Row]:
        row = start or Row.rounds(self.stage)
        if row.stage != self.stage:
            raise TouchError(f"{row} is not a stage {self.stage} row")
        out = [row]
        for leg in self.legs:
            lead = called_lead(leg.method.changes, leg.call, row)
            out.extend(lead[1:])
            row = lead[-1]
        return out

    @property
    def final_row(self) -> Row:
        return self.rows()[-1]

    def comes_round(self) -> bool:
        return self.final_row.is_rounds


def lead_heads_agree(first: Method, second: Method) -> bool:
    """Whether two methods can be spliced at a lead end.

    They have to leave the bells in the same places, or the line the band
    learnt for the next method starts from somewhere it does not expect. That
    is the same question a composer asks about whether one method's calling
    will ring to another, so there is one answer to it in core/leadheads.
    """
    return share_lead_heads(first, second)


def spliceable(methods: List[Method]) -> List[Tuple[str, str]]:
    """Every pair that will not splice, so a band knows before they try."""
    bad: List[Tuple[str, str]] = []
    for index, first in enumerate(methods):
        for second in methods[index + 1 :]:
            if not lead_heads_agree(first, second):
                bad.append((first.name, second.name))
    return bad


def build_spliced(
    methods: Dict[str, Method],
    order: str,
    calls: Optional[Dict[str, Call]] = None,
    calling: str = "",
) -> Spliced:
    """Assemble a spliced touch from initials and an optional calling.

    Bands write the order as initials, so YNCB is Yorkshire then a method
    beginning with N and so on. The calling runs alongside it, one symbol per
    lead, and where it is shorter the rest are plain.
    """
    by_initial = {name[0].upper(): method for name, method in methods.items()}
    legs: List[Leg] = []
    for index, initial in enumerate(order.strip().upper()):
        method = by_initial.get(initial)
        if method is None:
            raise TouchError(f"no method beginning with {initial!r}")
        symbol = calling[index] if index < len(calling) else "p"
        call = None if symbol == "p" else (calls or {}).get(symbol)
        if symbol != "p" and call is None:
            raise TouchError(f"no call written {symbol!r}")
        legs.append(Leg(method=method, call=call))
    return Spliced(legs=tuple(legs))
