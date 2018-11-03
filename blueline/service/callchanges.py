"""Call change touches, worked out for somebody who has to call one.

Three questions get asked, and they are the three a conductor asks standing
behind a band. What does this calling actually come to? How do I get from here
to Queens? And is this touch any good, meaning did it go anywhere or did it
wander about and end up back where it started.

Nothing here is stored. A call change touch is called on the spot and written
down afterwards, if at all.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from dataclasses import dataclass

from blueline.core.callchanges import (
    Call,
    CallChangeError,
    Style,
    calling_to,
    named_row,
    parse_calling,
    ring,
)
from blueline.core.music import name_of
from blueline.core.row import Row
from blueline.errors import BluelineError
from blueline.service.results import Result, invalid, succeeded

#: Longer than any touch a band stands behind. A wrong file is the usual
#: reason a calling is thousands of calls long.
MOST_CALLS = 2000


@dataclass(frozen=True)
class Rung:
    """One row the band stood on, and what got them there."""

    row: str
    call: str
    name: Optional[str]


@dataclass(frozen=True)
class CallChangeReport:
    """What a calling comes to."""

    stage: int
    calls: int
    rows: Tuple[Rung, ...]
    start: str
    finish: str
    came_round: bool
    named_reached: Tuple[str, ...]

    @property
    def stood_still(self) -> int:
        """Calls that changed nothing, which a conductor wants to know about."""
        return sum(1 for index, rung in enumerate(self.rows) if index and rung.call == "stand")

    def summary(self) -> str:
        ending = "came round" if self.came_round else f"finished on {self.finish}"
        return f"{self.calls} calls, {ending}"


def _rung(row: Row, call: Optional[Call]) -> Rung:
    return Rung(
        row=str(row),
        call="start" if call is None else str(call),
        name=name_of(row),
    )


def report_of(rows: List[Row], calls: Tuple[Call, ...]) -> CallChangeReport:
    made: List[Rung] = [_rung(rows[0], None)]
    for row, call in zip(rows[1:], calls):
        rung = _rung(row, call)
        if row == rows[len(made) - 1]:
            rung = Rung(row=rung.row, call="stand", name=rung.name)
        made.append(rung)

    reached = tuple(
        dict.fromkeys(rung.name for rung in made[1:] if rung.name is not None and rung.name)
    )
    return CallChangeReport(
        stage=rows[0].stage,
        calls=len(calls),
        rows=tuple(made),
        start=str(rows[0]),
        finish=str(rows[-1]),
        came_round=rows[-1].is_rounds,
        named_reached=reached,
    )


def prove(
    calling: str, stage: int, style: str = "down", start: str = ""
) -> Result[CallChangeReport]:
    """Ring a calling through and say where it went."""
    try:
        which = Style(style.strip().lower())
    except ValueError:
        return invalid(f"no such style of calling as {style!r}, try up or down")

    try:
        first = Row.parse(start) if start.strip() else Row.rounds(stage)
    except BluelineError as error:
        return invalid(str(error))
    if first.stage != stage:
        return invalid(f"{first} is not on {stage} bells")

    try:
        calls = parse_calling(calling, which)
    except CallChangeError as error:
        return invalid(str(error))
    if len(calls) > MOST_CALLS:
        return invalid(f"{len(calls)} calls is more than anybody stands behind")

    try:
        rows = ring(first, calls)
    except CallChangeError as error:
        return invalid(str(error))
    return succeeded(report_of(rows, calls))


def how_to_get_to(target: str, stage: int, start: str = "") -> Result[CallChangeReport]:
    """The calls that take a band from where they are to a named change."""
    try:
        first = Row.parse(start) if start.strip() else Row.rounds(stage)
    except BluelineError as error:
        return invalid(str(error))
    if first.stage != stage:
        return invalid(f"{first} is not on {stage} bells")

    wanted = target.strip()
    try:
        want = named_row(wanted, stage) if not wanted[:1].isdigit() else Row.parse(wanted)
    except (CallChangeError, BluelineError, IndexError) as error:
        return invalid(str(error) or "nowhere to go")
    if want.stage != stage:
        return invalid(f"{want} is not on {stage} bells")

    calls = calling_to(first, want)
    return succeeded(report_of(ring(first, calls), calls))


def said(report: CallChangeReport, style: str = "down") -> Result[List[str]]:
    """The calling written out the way the conductor would say it."""
    try:
        which = Style(style.strip().lower())
    except ValueError:
        return invalid(f"no such style of calling as {style!r}, try up or down")

    spoken: List[str] = []
    for rung in report.rows[1:]:
        if rung.call in {"start", "stand"}:
            spoken.append(rung.call)
            continue
        moving, after = (int(part) for part in rung.call.split(" to "))
        spoken.append(Call(moving=moving, after=after).said(which))
    return succeeded(spoken)
