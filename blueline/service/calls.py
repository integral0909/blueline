"""Calling a touch the way a conductor says it, by position.

Two ways in, because there are two ways somebody has it. Either they have the
positions as a list, which is what a program produces, or they have the line
off the back of a peal card, which is what a person has.
"""

from __future__ import annotations

from typing import List, Tuple

from dataclasses import dataclass

from blueline.core.bobs import PositionError, calling_from, positions_in, positions_of
from blueline.core.shorthand import ShorthandError, format_shorthand, parse_shorthand
from blueline.db.repositories import MethodRepository, to_method
from blueline.service.lookups import stored_method
from blueline.service.proving import TouchReport, prove
from blueline.service.results import Result, invalid, succeeded


@dataclass(frozen=True)
class PositionView:
    """A calling position, as anybody wants to read it."""

    name: str
    lead: int
    tenor_place: int


def positions(repository: MethodRepository, title: str) -> Result[List[PositionView]]:
    """The named calling positions in a method's plain course."""
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    return succeeded(
        [
            PositionView(name=p.name, lead=p.lead, tenor_place=p.tenor_place)
            for p in positions_of(to_method(stored))
        ]
    )


def prove_positions(
    repository: MethodRepository,
    title: str,
    called: List[str],
) -> Result[TouchReport]:
    """Prove a touch written the way a conductor calls it.

    Wrong, Home, Home rather than one symbol per lead. The two are the same
    thing and turning one into the other by hand is where mistakes come from.
    """
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    method = to_method(stored)
    try:
        calling = calling_from(method, called)
    except PositionError as error:
        return invalid(str(error))
    return prove(repository, title, calling)


def calling_as_positions(
    repository: MethodRepository,
    title: str,
    calling: str,
) -> Result[List[str]]:
    """Read a calling back as the positions a conductor would say."""
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    return succeeded(positions_in(to_method(stored), calling))


@dataclass(frozen=True)
class PrintedView:
    """A printed composition, read and then rung through."""

    printed: str
    tidied: str
    positions: Tuple[str, ...]
    parts: int
    calling: str
    touch: TouchReport

    @property
    def calls(self) -> int:
        return len(self.positions) * self.parts

    def summary(self) -> str:
        return f"{self.tidied}: {self.touch.summary()}"


def prove_printed(
    repository: MethodRepository,
    title: str,
    printed: str,
) -> Result[PrintedView]:
    """Prove a composition written the way it is published.

    "W 2H x3" rather than a list of positions, and rather than one symbol per
    lead. Everything between the printed line and the touch is done here, so a
    caller with a peal card has one call to make.
    """
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()

    try:
        composition = parse_shorthand(printed)
    except ShorthandError as error:
        return invalid(str(error))

    method = to_method(stored)
    try:
        calling = calling_from(method, list(composition.expanded()))
    except PositionError as error:
        return invalid(str(error))

    proved = prove(repository, title, calling)
    if not proved.ok:
        return Result(failure=proved.failure)

    return succeeded(
        PrintedView(
            printed=printed.strip(),
            tidied=format_shorthand(composition),
            positions=composition.positions,
            parts=composition.parts,
            calling=calling,
            touch=proved.unwrap(),
        )
    )
