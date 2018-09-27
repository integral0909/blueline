"""Naming a call by where it comes, which is how conductors actually work.

A conductor does not say "bob at the fourth lead". They say Wrong, or Home, or
Before, and every ringer in the band knows which lead that is because the name
says where the tenor is. Home is the tenor coming back to where it started;
Wrong is a lead earlier; Before is the tenor about to run in.

Naming the positions is the difference between a composition somebody can call
and a list of leads they have to count through. Getting them right matters:
call Wrong where you meant Home and the whole thing falls apart.
"""

from __future__ import annotations

from typing import List, Tuple

from dataclasses import dataclass

from blueline.core.method import Method
from blueline.core.row import Row
from blueline.errors import BluelineError


class PositionError(BluelineError):
    """A calling position that does not exist in this method."""


#: What a calling position is called, by where the tenor stands at the lead
#: head. Named from the tenor's place rather than from how far through the
#: course the lead is: Home is the tenor back where it started, Wrong is one
#: place below it, Middle one below that, and Before is the tenor about to run
#: in at the front.
def name_for_place(place: int, stage: int) -> str:
    """What a conductor calls the position with the tenor in this place."""
    if place == stage:
        return "Home"
    if place == stage - 1:
        return "Wrong"
    if place == stage - 2:
        return "Middle"
    if place == 2:
        return "Before"
    return f"{_ordinal(place)}s"


def _ordinal(place: int) -> str:
    words = {3: "Third", 4: "Fourth", 5: "Fifth", 6: "Sixth", 7: "Seventh"}
    return words.get(place, str(place))


@dataclass(frozen=True)
class Position:
    """A named place in the course where a call can be made."""

    name: str
    lead: int
    tenor_place: int

    def __str__(self) -> str:
        return f"{self.name} (lead {self.lead}, tenor in {self.tenor_place})"


def tenor_places(method: Method) -> Tuple[int, ...]:
    """Where the tenor stands at each lead head of the plain course."""
    tenor = method.stage
    row = Row.rounds(method.stage)
    places: List[int] = []
    for _ in range(method.leads_in_course):
        row = row.transposed_by(method.lead_head)
        places.append(row.place_of(tenor))
    return tuple(places)


def positions_of(method: Method) -> List[Position]:
    """Every named calling position in the plain course."""
    return [
        Position(
            name=name_for_place(place, method.stage),
            lead=index + 1,
            tenor_place=place,
        )
        for index, place in enumerate(tenor_places(method))
    ]


def position_named(method: Method, name: str) -> Position:
    """The position with this name, or a complaint listing what there is."""
    wanted = name.strip().lower()
    for position in positions_of(method):
        if position.name.lower() == wanted:
            return position
    known = ", ".join(position.name for position in positions_of(method))
    raise PositionError(f"no calling position called {name!r}, try one of {known}")


def calling_from(method: Method, positions: List[str], symbol: str = "-") -> str:
    """Turn a list of calling positions into one symbol per lead.

    A conductor writes Wrong, Home, Home. Two Homes running means two courses,
    because Home comes once in each, so the calling runs on into another course
    whenever the next position is not further through than the last. Collapsing
    them into one course would have quietly turned three calls into two.
    """
    leads = len(tenor_places(method))
    if not positions:
        return "p" * leads

    wanted = [position_named(method, name).lead for name in positions]
    called: List[int] = []
    course = 0
    previous = 0
    for lead in wanted:
        if lead <= previous:
            course += 1
        called.append(course * leads + lead)
        previous = lead

    total = (course + 1) * leads
    marked = set(called)
    return "".join(symbol if lead in marked else "p" for lead in range(1, total + 1))


def positions_in(method: Method, calling: str, plain: str = "p") -> List[str]:
    """Read a calling back as the positions a conductor would say.

    Runs on past the end of a course, so a calling of two courses comes back
    as the positions in both rather than only the first.
    """
    found = positions_of(method)
    if not found:
        return []
    return [
        found[index % len(found)].name
        for index, symbol in enumerate(calling.strip())
        if symbol != plain
    ]
