"""Proving a touch, and reporting what it did.

Assembling a calling into a touch and ringing it through. Searching for a
calling is in search; naming the positions a conductor calls by is in calls.
"""

from __future__ import annotations

from typing import Dict, Tuple

from dataclasses import dataclass

from blueline.core.calls import Call, grandsire_calls, plain_bob_calls
from blueline.core.method import Method
from blueline.core.music import MusicCount
from blueline.core.peals import Standing
from blueline.core.touch import Touch, parse_calling, plain_course, repeat
from blueline.core.truth import Repeat, extent_length, is_extent
from blueline.db.repositories import MethodRepository, to_method
from blueline.errors import BluelineError
from blueline.service.lookups import stored_method
from blueline.service.reports import Outcome, outcome_of
from blueline.service.results import Result, invalid, succeeded

#: Methods called the Grandsire way rather than the Plain Bob way.
GRANDSIRE_NAMES = frozenset({"Grandsire", "Reverse Grandsire", "Double Grandsire"})

#: Spellings people use for a bob and a single besides the usual symbols.
ALIASES = {"b": "-", "B": "-", "S": "s", ".": "p", "P": "p"}


@dataclass(frozen=True)
class TouchReport:
    """What a touch does, once somebody has rung it through."""

    title: str
    calling: str
    outcome: Outcome
    is_extent: bool
    extent_length: int

    #: Read through to the outcome, so callers do not have to know it is there.
    @property
    def leads(self) -> int:
        return self.outcome.leads

    @property
    def length(self) -> int:
        return self.outcome.length

    @property
    def comes_round(self) -> bool:
        return self.outcome.comes_round

    @property
    def is_true(self) -> bool:
        return self.outcome.is_true

    @property
    def repeats(self) -> Tuple[Repeat, ...]:
        return self.outcome.repeats

    @property
    def music(self) -> MusicCount:
        return self.outcome.music

    @property
    def final_row(self) -> str:
        return self.outcome.final_row

    @property
    def standing(self) -> Standing:
        return self.outcome.standing

    @property
    def is_ringable(self) -> bool:
        return self.outcome.is_ringable

    def summary(self) -> str:
        return self.outcome.summarise()


def calls_for(method: Method) -> Dict[str, Call]:
    """The calls a method is rung with.

    Grandsire and its relatives are called a change before the lead end, which
    is a different set from the fourths place bob everything else uses. Picking
    on the name is crude and it is what ringers do.

    The aliases are here because a calling written with dashes is awkward to
    type on a command line, so b for a bob has to work as well.
    """
    calls = (
        grandsire_calls(method.stage)
        if method.name in GRANDSIRE_NAMES
        else plain_bob_calls(method.stage)
    )
    for alias, real in ALIASES.items():
        if real in calls:
            calls[alias] = calls[real]
    return calls


def build(method: Method, calling: str, times: int = 1) -> Result[Touch]:
    """Assemble a touch from a calling written as one symbol per lead."""
    try:
        block = parse_calling(method, calls_for(method), calling)
        return succeeded(repeat(block, times) if times > 1 else block)
    except BluelineError as error:
        return invalid(str(error))


def report_on(touch: Touch, title: str) -> TouchReport:
    """Ring the touch through and say what happened."""
    return TouchReport(
        title=title,
        calling=touch.calling,
        outcome=outcome_of(touch.rows(), touch.leads),
        is_extent=is_extent(touch),
        extent_length=extent_length(touch.stage),
    )


def prove(
    repository: MethodRepository,
    title: str,
    calling: str,
    times: int = 1,
) -> Result[TouchReport]:
    """Prove a touch of a stored method."""
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    if times < 1:
        return invalid(f"cannot ring a block {times} times")
    built = build(to_method(stored), calling, times)
    if not built.ok:
        return Result(failure=built.failure)
    return succeeded(report_on(built.unwrap(), stored.title))


def course_of(repository: MethodRepository, title: str) -> Result[TouchReport]:
    """The plain course, reported the same way a touch is."""
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    return succeeded(report_on(plain_course(to_method(stored)), stored.title))
