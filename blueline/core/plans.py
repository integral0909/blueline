"""Planning a practice, which is a different problem from composing.

A conductor running a Tuesday night has a band, a tower and an hour. What they
need is a list of things that band can actually ring in that time, ordered so
the evening goes somewhere: something to warm up on, something everybody can
do, then whatever the band is learning.

The constraint that does the work is the band. Six people cannot ring major
however much they would like to, and a method nobody has learnt is not a
choice. Everything else is arranging what is left into an order.
"""

from __future__ import annotations

from typing import List, Tuple

from dataclasses import dataclass
from datetime import timedelta

from blueline.core.method import Method
from blueline.core.ringing_up import Session
from blueline.errors import BluelineError


class PlanError(BluelineError):
    """A practice that cannot be planned as asked."""


@dataclass(frozen=True)
class Item:
    """One thing to ring, and how long it will take."""

    method: Method
    changes: int
    minutes: int

    @property
    def title(self) -> str:
        return f"{self.method.name} {self.method.stage}"

    def __str__(self) -> str:
        return f"{self.changes} of {self.method.name} ({self.minutes}m)"


@dataclass(frozen=True)
class Plan:
    """An evening's ringing."""

    items: Tuple[Item, ...]
    ringers: int
    available: timedelta
    left_over: timedelta

    @property
    def minutes(self) -> int:
        return sum(item.minutes for item in self.items)

    @property
    def changes(self) -> int:
        return sum(item.changes for item in self.items)

    def summary(self) -> str:
        if not self.items:
            return "nothing this band can ring in the time"
        spare = int(round(self.left_over.total_seconds() / 60))
        return f"{len(self.items)} touches, {self.minutes} minutes, {spare} to spare"


def ringable_by(methods: List[Method], ringers: int) -> List[Method]:
    """The methods a band of this size can actually ring.

    A band can ring its own number of bells, and one fewer where that is odd,
    because the extra person covers. Anything above is out however well they
    know it.
    """
    if ringers < 3:
        raise PlanError(f"{ringers} is not enough people to ring anything")
    return [
        method
        for method in methods
        if method.stage == ringers or (method.stage == ringers - 1 and method.stage % 2 == 1)
    ]


def course_item(method: Method, speed: float = 30.0) -> Item:
    """A plain course of a method, timed."""
    session = Session(bells=method.stage, changes=method.course_length, peal_speed=speed)
    minutes = int(round(session.ringing_time.total_seconds() / 60))
    return Item(method=method, changes=method.course_length, minutes=max(1, minutes))


def plan_practice(
    methods: List[Method],
    ringers: int,
    minutes: int,
    speed: float = 30.0,
) -> Plan:
    """Fill the time with plain courses the band can ring.

    Shortest first, so the evening starts on something everybody gets right
    and the long one only goes in if there is really room. A conductor can
    always reorder; what they cannot do is invent the time.
    """
    if minutes < 1:
        raise PlanError("a practice has to be longer than nothing")
    available = timedelta(minutes=minutes)

    candidates = ringable_by(methods, ringers)
    items = sorted(
        (course_item(method, speed) for method in candidates),
        key=lambda item: (item.minutes, item.title),
    )

    chosen: List[Item] = []
    spent = 0
    for item in items:
        if spent + item.minutes > minutes:
            continue
        chosen.append(item)
        spent += item.minutes

    return Plan(
        items=tuple(chosen),
        ringers=ringers,
        available=available,
        left_over=available - timedelta(minutes=spent),
    )
