"""A touch, which is a method rung for a while with calls in it.

What gets performed is not a method but a touch of one: so many leads, with a
bob or a single called at some of them, ending when rounds comes back. This is
the thing a conductor holds in their head and the thing a composer writes down,
so it is worth being a type rather than a loop somewhere.

The calling is held as one entry per lead, with None meaning a plain lead. That
is more verbose than the way callings are usually written, where only the calls
are named and the plains are counted, but it makes the touch and its rows line
up one to one and every awkward question about where a call lands goes away.

Nothing here proves anything. Expanding a touch into rows and deciding whether
those rows are any good are two jobs, and truth.py does the second.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from dataclasses import dataclass

from blueline.core.calls import PLAIN, Call, called_lead
from blueline.core.method import Method
from blueline.core.row import Row


class TouchError(ValueError):
    """A touch that cannot be rung as written."""


@dataclass(frozen=True)
class Touch:
    """A method, and what is called at each of its leads."""

    method: Method
    calls: Tuple[Optional[Call], ...]

    def __post_init__(self) -> None:
        for call in self.calls:
            if call is not None and call.stage != self.method.stage:
                raise TouchError(
                    f"{call.name} is stage {call.stage}, {self.method.name} is stage "
                    f"{self.method.stage}"
                )

    @property
    def stage(self) -> int:
        return self.method.stage

    @property
    def leads(self) -> int:
        return len(self.calls)

    @property
    def length(self) -> int:
        """How many changes are rung, which is what a touch is measured in."""
        return self.leads * self.method.lead_length

    def rows(self, start: Optional[Row] = None) -> List[Row]:
        """Every row of the touch, opening rounds first.

        There is one more row here than the touch is long, because the opening
        row is not something anybody rang a change to get to.
        """
        row = start or Row.rounds(self.stage)
        if row.stage != self.stage:
            raise TouchError(f"{row} is not a stage {self.stage} row")
        out = [row]
        for call in self.calls:
            lead = called_lead(self.method.changes, call, row)
            out.extend(lead[1:])
            row = lead[-1]
        return out

    @property
    def final_row(self) -> Row:
        return self.rows()[-1]

    def comes_round(self) -> bool:
        """Whether the touch ends where it started, which it has to."""
        return self.final_row.is_rounds

    @property
    def calling(self) -> str:
        """The calling written out as one symbol per lead."""
        return "".join(PLAIN if call is None else call.symbol for call in self.calls)


def plain_course(method: Method) -> Touch:
    """The touch you get by calling nothing at all."""
    return Touch(method=method, calls=(None,) * method.leads_in_course)


def parse_calling(method: Method, available: Dict[str, Call], text: str) -> Touch:
    """Read a calling written as one symbol per lead, such as -p-s.

    Anything not recognised is refused rather than quietly taken for a plain
    lead, because a typo in a calling that rings as something else is a nasty
    way to find out.
    """
    calls: List[Optional[Call]] = []
    for symbol in text.strip():
        if symbol.isspace():
            continue
        if symbol == PLAIN:
            calls.append(None)
            continue
        call = available.get(symbol)
        if call is None:
            raise TouchError(f"no call written {symbol!r} for {method.name}")
        calls.append(call)
    if not calls:
        raise TouchError("a touch has to have at least one lead in it")
    return Touch(method=method, calls=tuple(calls))


def repeat(touch: Touch, times: int) -> Touch:
    """Ring the same block of leads over again, the way a composition does."""
    if times < 1:
        raise TouchError(f"cannot ring a block {times} times")
    return Touch(method=touch.method, calls=touch.calls * times)
