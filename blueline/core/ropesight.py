"""What a ringer sees, which is not the same as what the rows say.

A ringer does not read rows. They watch the bells either side of them and count
their place, and what they need to know about a method is who they follow at
each blow and where the pieces of work fall. A library that only produced rows
would be no use for learning from.

Following is the thing bands talk about most. If the bell before you in one row
is the bell before you in the next, you are following the same bell twice, and
that is a dodge. Working that out from the rows is what turns a grid into
something a ringer can hold in their head.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from dataclasses import dataclass

from blueline.core.method import Method
from blueline.core.row import Row
from blueline.errors import MethodError


@dataclass(frozen=True)
class Blow:
    """One blow of one bell, and what was going on around it."""

    row: int
    place: int
    follows: Optional[int]
    followed_by: Optional[int]

    @property
    def is_leading(self) -> bool:
        return self.place == 1

    @property
    def is_lying(self) -> bool:
        return self.followed_by is None


def follows_at(row: Row, bell: int) -> Optional[int]:
    """The bell struck immediately before this one, or none if it is leading."""
    place = row.place_of(bell)
    return None if place == 1 else row[place - 1]


def followed_by_at(row: Row, bell: int) -> Optional[int]:
    """The bell struck immediately after, or none if it is lying behind."""
    place = row.place_of(bell)
    return None if place == row.stage else row[place + 1]


def blows_of(rows: List[Row], bell: int) -> List[Blow]:
    """Every blow a bell strikes, with who it was following."""
    return [
        Blow(
            row=index,
            place=row.place_of(bell),
            follows=follows_at(row, bell),
            followed_by=followed_by_at(row, bell),
        )
        for index, row in enumerate(rows)
    ]


def dodges_in(blows: List[Blow]) -> List[int]:
    """Where a bell dodges, given as the middle row of the dodge.

    A dodge is a step one way and straight back: three blows going a, b, a with
    a and b next to each other. Following the same bell twice looked like the
    right test and is not, because a bell standing still follows the same bell
    too and that is making a place, which reads quite differently on a rope.

    Found dodges do not overlap. The pattern a, b, a, b is the one dodge every
    ringer would count, and matching every window would call it two.
    """
    places = [blow.place for blow in blows]
    found: List[int] = []
    index = 0
    while index + 2 < len(places):
        first, middle, last = places[index], places[index + 1], places[index + 2]
        if first == last and first != middle:
            found.append(blows[index + 1].row)
            index += 2
            continue
        index += 1
    return found


def places_made_in(blows: List[Blow]) -> List[int]:
    """Where a bell stands still, given as the row it stands into."""
    return [
        later.row
        for earlier, later in zip(blows, blows[1:])
        if earlier.place == later.place
    ]


def leads_in(blows: List[Blow]) -> List[int]:
    """Every row the bell is leading in."""
    return [blow.row for blow in blows if blow.is_leading]


def lies_in(blows: List[Blow]) -> List[int]:
    """Every row the bell is lying behind in."""
    return [blow.row for blow in blows if blow.is_lying]


def work_of(method: Method, bell: int) -> Dict[str, List[int]]:
    """The pieces of work a bell does through a lead, by name."""
    if bell < 1 or bell > method.stage:
        raise MethodError(f"{method.name} has no bell {bell}")
    # The closing row of a lead is the opening row of the next, so counting it
    # here would have the treble leading three times in a lead of Plain Bob.
    blows = blows_of(method.lead_rows()[:-1], bell)
    return {
        "leads": leads_in(blows),
        "lies": lies_in(blows),
        "dodges": dodges_in(blows),
        "places": places_made_in(blows),
    }


def rope_order(row: Row) -> List[int]:
    """The bells in the order the ropes go down, which is the row itself.

    Named separately because that is what a ringer calls it, and because a
    caller asking for the rope order is asking a different question from one
    asking for the row even though the answer is the same.
    """
    return list(row.bells)
