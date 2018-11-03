"""Call change ringing, which is the other half of the exercise.

Method ringing changes the order every row by a rule everybody has learnt. Call
change ringing changes it when the conductor says so, one pair at a time, and
the band rings the same row over and over until told otherwise. It is what most
towers ring most of the time, it is what every learner rings first, and in
Devon it is what a competition is judged on.

A call names two bells and puts one after the other. Two ways of saying it are
in use and they mean different things:

    "three to four"   up-call:   put the three directly after the four
    "four to three"   down-call: the same pair the other way about

Devon calls up, most of the rest of the country calls down, and a band that
mixes the two ends up standing still. Both are here, and which one a touch is
in is a property of the touch rather than of each call, because a conductor
does not switch halfway.

Named changes get rung by name: Queens, Kings, Tittums. Those are rows, and
core.music already knows them because it counts them as music. The useful
question here is how to get to one from where the band is standing, which is
what calling_to works out.
"""

from __future__ import annotations

from typing import List, Tuple

from dataclasses import dataclass
from enum import Enum

from blueline.core.music import NAMED_ROWS
from blueline.core.row import Row
from blueline.errors import BluelineError


class CallChangeError(BluelineError):
    """A call that cannot be made from the row the band is standing on."""


class Style(str, Enum):
    """Which way round a conductor names a pair."""

    UP = "up"
    DOWN = "down"


@dataclass(frozen=True)
class Call:
    """One call: a bell, and the bell it is being put after."""

    moving: int
    after: int

    def __post_init__(self) -> None:
        if self.moving == self.after:
            raise CallChangeError(f"the {self.moving} cannot be called after itself")

    def said(self, style: Style = Style.DOWN) -> str:
        """How a conductor would say it."""
        if style is Style.UP:
            return f"{self.after} to {self.moving}"
        return f"{self.moving} to {self.after}"

    def __str__(self) -> str:
        return self.said()


def parse_call(text: str, style: Style = Style.DOWN) -> Call:
    """Read a call somebody wrote down, such as "3 to 4"."""
    words = text.replace(" to ", " ").split()
    if len(words) != 2:
        raise CallChangeError(f"{text!r} is not a call")
    try:
        first, second = (int(word) for word in words)
    except ValueError:
        raise CallChangeError(f"{text!r} does not name two bells") from None
    if style is Style.UP:
        return Call(moving=second, after=first)
    return Call(moving=first, after=second)


def parse_calling(text: str, style: Style = Style.DOWN) -> Tuple[Call, ...]:
    """A whole touch, one call to a line or separated by semicolons."""
    parts = [part.strip() for line in text.splitlines() for part in line.split(";")]
    return tuple(parse_call(part, style) for part in parts if part)


def apply_call(row: Row, call: Call) -> Row:
    """Ring the call, giving the row the band comes to.

    Only adjacent pairs can be swapped, because that is all a band can
    physically do in one row. Calling a bell after one it is not next to is a
    call the band cannot ring, and saying so is more use than quietly moving
    the bell several places.
    """
    try:
        moving = row.place_of(call.moving)
        after = row.place_of(call.after)
    except BluelineError as error:
        raise CallChangeError(f"{call}: {error}") from error

    if moving == after + 1:
        # Already where it was asked to go. Conductors do call these, usually
        # by mistake, and the band simply rings the same row again.
        return row
    if moving != after - 1:
        raise CallChangeError(f"{call}: they are not next to each other")
    return row.swap(moving)


def ring(start: Row, calls: Tuple[Call, ...]) -> List[Row]:
    """Every row the band stands on, starting from where they began."""
    rows = [start]
    for call in calls:
        rows.append(apply_call(rows[-1], call))
    return rows


def calling_to(start: Row, target: Row) -> Tuple[Call, ...]:
    """Calls that take a band from one row to another.

    Worked out as a bubble sort, which is not a clever algorithm and is
    exactly what a conductor does: find a bell that is out of place, call it
    where it belongs, look again. It gives more calls than the theoretical
    minimum in some cases and every one of them is a call a band can ring.
    """
    if start.stage != target.stage:
        raise CallChangeError("both rows have to be on the same number of bells")

    calls: List[Call] = []
    current = start
    for place in range(1, current.stage):
        wanted = target.bells[place - 1]
        while current.bells[place - 1] != wanted:
            at = current.place_of(wanted)
            # The bell in front of it is the one that moves. Calling the
            # wanted bell after its neighbour would name the pair it is
            # already in, which is a call the band rings by standing still.
            calls.append(Call(moving=current.bells[at - 2], after=wanted))
            current = current.swap(at - 1)
    return tuple(calls)


def named_row(name: str, stage: int) -> Row:
    """One of the changes a band rings by name.

    The rows themselves live in core.music, which already knew what queens and
    tittums are because it counts them as music. A second set of definitions
    here would be a second set to keep right.
    """
    wanted = name.strip().lower()
    if wanted not in NAMED_ROWS:
        raise CallChangeError(f"nothing called {name!r} is rung by name")
    return NAMED_ROWS[wanted](stage)


def calling_to_named(start: Row, name: str) -> Tuple[Call, ...]:
    """How to get from where the band is to a change they ring by name."""
    return calling_to(start, named_row(name, start.stage))
