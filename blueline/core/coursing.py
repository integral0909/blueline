"""Coursing order, which is how conductors keep track of a touch.

Bells do not wander about at random through a plain course. Each one follows
another in a fixed ring, and that ring is the coursing order. A conductor who
knows it can tell at a glance which bell is about to do what, and a composer
writes calls in terms of what they do to it rather than in terms of rows.

It falls out of the lead head. Take the cycle of working bells in the lead head
permutation, read it backwards and start at the tenor, and you have the order
every ringer would write down. At Plain Bob Major that comes to 8 7 5 3 2 4 6,
which is the first thing anybody learns about the method after the line.
"""

from __future__ import annotations

from typing import List, Tuple

from blueline.core.method import Method
from blueline.core.row import Row


class CoursingError(ValueError):
    """A method whose coursing order does not mean anything."""


def coursing_places(stage: int) -> Tuple[int, ...]:
    """The places to read off a lead head, in the order a conductor reads them.

    Odd places from the back downwards, then even places from the front up.
    Leading is left out because the bell there is hunting, not coursing.
    """
    odd = [place for place in range(stage, 1, -1) if place % 2 == 1]
    even = [place for place in range(2, stage + 1) if place % 2 == 0]
    return tuple(odd + even)


def coursing_order_of(lead_head: Row, hunt_bells: Tuple[int, ...] = ()) -> Tuple[int, ...]:
    """The ring of working bells, read the way a conductor would say it.

    Reading the cycles of the lead head permutation looks like it ought to
    work and does not. It gives the order bells replace each other at lead
    heads, which for Cambridge is a different ring from the coursing order
    every ringer would tell you. Reading the places off the row is the rule
    that actually holds.
    """
    hunting = set(hunt_bells)
    read = [lead_head[place] for place in coursing_places(lead_head.stage)]
    working = tuple(bell for bell in read if bell not in hunting)
    if not working:
        raise CoursingError(f"{lead_head} leaves no bells coursing")
    tenor = max(working)
    start = working.index(tenor)
    return working[start:] + working[:start]


def coursing_order(method: Method) -> Tuple[int, ...]:
    """The coursing order of a method's plain course."""
    return coursing_order_of(method.lead_head, method.hunt_bells)


def as_text(order: Tuple[int, ...]) -> str:
    """The order written out the way it is said, such as 87532 46."""
    from blueline.core.stage import bell_symbol

    return "".join(bell_symbol(bell) for bell in order)


def courses_after(order: Tuple[int, ...], bell: int) -> int:
    """The bell that follows another round the coursing order."""
    if bell not in order:
        raise CoursingError(f"bell {bell} is not coursing")
    return order[(order.index(bell) + 1) % len(order)]


def courses_before(order: Tuple[int, ...], bell: int) -> int:
    if bell not in order:
        raise CoursingError(f"bell {bell} is not coursing")
    return order[(order.index(bell) - 1) % len(order)]


def coursing_pairs(order: Tuple[int, ...]) -> List[Tuple[int, int]]:
    """Every bell and the one that courses after it, right round the ring."""
    return [(bell, courses_after(order, bell)) for bell in order]


def rotate_to(order: Tuple[int, ...], bell: int) -> Tuple[int, ...]:
    """The same ring written starting from a different bell."""
    if bell not in order:
        raise CoursingError(f"bell {bell} is not coursing")
    start = order.index(bell)
    return order[start:] + order[:start]


def is_same_ring(first: Tuple[int, ...], second: Tuple[int, ...]) -> bool:
    """Whether two coursing orders are the same ring written differently.

    A coursing order has no beginning, so 87532 46 and 46 87532 are the same
    thing. Comparing them as written would say they were not.
    """
    if len(first) != len(second) or set(first) != set(second):
        return False
    return rotate_to(second, first[0]) == first
