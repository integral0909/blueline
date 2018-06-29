"""What kind of method this is.

Ringers sort methods by what the treble does. If no bell stays put at the lead
head then every bell rings the same line and the method is a principle, which
is why Stedman is not a Plain Bob sort of thing at all. Otherwise the treble
either hunts plainly up and down, or it dodges its way up in pairs of places,
and those two give the big families.

Inside the treble dodging family the split is finer and turns on what the other
bells are doing while the treble crosses from one pair of places to the next.
Places made there make the method harder and more interesting. All of them and
it is Surprise, some of them Delight, none at all and it is only Treble Bob.
"""

from __future__ import annotations

from typing import List, Optional

from collections import Counter
from dataclasses import dataclass

from blueline.core.method import Method
from blueline.core.notation import Change


@dataclass(frozen=True)
class Classification:
    """What a method is, in the words that go into its title."""

    kind: str
    family: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.family} {self.kind}" if self.family else self.kind


def blows_per_place(method: Method) -> Counter[int]:
    """How many blows the treble strikes in each place through a lead."""
    path = method.path_of(1)[:-1]
    return Counter(path)


def treble_hunts_plainly(method: Method) -> bool:
    """Whether the treble goes straight up and straight back down."""
    counts = blows_per_place(method)
    if set(counts) != set(range(1, method.stage + 1)):
        return False
    return all(count == 2 for count in counts.values())


def treble_dodges(method: Method) -> bool:
    """Whether the treble takes four blows in every place, dodging as it goes."""
    counts = blows_per_place(method)
    if set(counts) != set(range(1, method.stage + 1)):
        return False
    return all(count == 4 for count in counts.values())


def cross_section_indices(method: Method) -> List[int]:
    """Where in the lead the treble crosses from one pair of places to the next.

    These are the changes worth looking at, because what the back bells are
    doing while the treble goes by is what separates Surprise from the rest.
    """
    path = method.path_of(1)
    found: List[int] = []
    for index in range(len(path) - 1):
        lower, upper = path[index], path[index + 1]
        if abs(upper - lower) != 1:
            continue
        higher = max(lower, upper)
        if higher % 2 == 1:
            found.append(index)
    return found


def has_internal_places(change: Change) -> bool:
    """Whether a change makes a place anywhere but the front or the back."""
    return any(1 < place < change.stage for place in change.places)


def internal_places_at_cross_sections(method: Method) -> List[bool]:
    """For each cross section, whether anybody made an internal place."""
    return [has_internal_places(method.changes[index]) for index in cross_section_indices(method)]


def classify_treble_dodging(method: Method) -> Classification:
    made = internal_places_at_cross_sections(method)
    if made and all(made):
        return Classification("Surprise")
    if any(made):
        return Classification("Delight")
    return Classification("Treble Bob")


def internal_places_away_from_the_treble(method: Method) -> bool:
    """Whether an internal place is made while the treble is out in the middle.

    Places at the lead end and the half lead do not count. Every plain method
    has to do something when the treble reaches the front or the back, and
    seconds place at the lead end is what makes Plain Bob Plain Bob rather than
    making it a Place method.
    """
    path = method.path_of(1)
    for index, change in enumerate(method.changes):
        before, after = path[index], path[index + 1]
        at_an_end = 1 in (before, after) or method.stage in (before, after)
        if at_an_end:
            continue
        if has_internal_places(change):
            return True
    return False


def classify(method: Method) -> Classification:
    """Sort a method into the family its title would name it by."""
    if not method.hunt_bells:
        return Classification("Principle")
    if treble_hunts_plainly(method):
        if internal_places_away_from_the_treble(method):
            return Classification("Place")
        return Classification("Bob")
    if treble_dodges(method):
        return classify_treble_dodging(method)
    counts = blows_per_place(method)
    if set(counts.values()) == {2, 4}:
        return Classification("Alliance")
    if all(count % 2 == 0 for count in counts.values()):
        return Classification("Treble Place")
    return Classification("Hybrid")
