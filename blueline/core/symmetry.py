"""The symmetries a method's notation can have.

Nearly every method that gets rung is palindromic: the notation reads the same
backwards about two points in the lead, which is why it can be written as half
a lead and a comma. That is not a tidiness thing. A symmetric method is easier
to learn because the second half of the line is the first half backwards, and
composers lean on it too.

The point of symmetry is not always the half lead. Grandsire is symmetric about
the change where the treble leads rather than about the middle of the lead, so
looking only at the obvious place would say it was asymmetric when every ringer
knows it is not. Every rotation has to be tried.

Rotational symmetry is a different animal. There the second half of the lead is
the first half turned upside down, so a place in seconds becomes a place in
sevenths at major. A method with both is called double.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from blueline.core.notation import Change


def mirror_change(change: Change) -> Change:
    """Turn a change upside down, so a place in seconds becomes one at the back."""
    stage = change.stage
    places = tuple(sorted(stage + 1 - place for place in change.places))
    return Change(places, stage)


def rotate(changes: List[Change], by: int) -> List[Change]:
    """Read the notation starting from a different point in the lead."""
    if not changes:
        return []
    step = by % len(changes)
    return changes[step:] + changes[:step]


def reflects_about_change(changes: List[Change], index: int) -> bool:
    """Whether the notation reads the same both ways about one change.

    This is where a method's symmetry actually sits. Plain Bob reflects about
    the half lead change and about the lead end change, and those changes map
    to themselves rather than to a neighbour.
    """
    count = len(changes)
    if count == 0:
        return False
    return all(
        changes[(index + step) % count] == changes[(index - step) % count] for step in range(count)
    )


def reflects_about_gap(changes: List[Change], index: int) -> bool:
    """Whether the notation reflects about the join after a change."""
    count = len(changes)
    if count == 0:
        return False
    return all(
        changes[(index + 1 + step) % count] == changes[(index - step) % count]
        for step in range(count)
    )


def palindromic_axes(changes: List[Change]) -> Tuple[int, ...]:
    """Every axis the notation reflects about, as doubled indices.

    An even number means the axis runs through that change, an odd one means it
    runs through the join after it. Doubling keeps both kinds in one list
    without needing halves.
    """
    axes: List[int] = []
    for index in range(len(changes)):
        if reflects_about_change(changes, index):
            axes.append(index * 2)
        if reflects_about_gap(changes, index):
            axes.append(index * 2 + 1)
    return tuple(sorted(axes))


def is_palindromic(changes: List[Change]) -> bool:
    return bool(palindromic_axes(changes))


def is_rotational(changes: List[Change]) -> bool:
    """Whether the second half of the lead is the first half turned over."""
    count = len(changes)
    if count == 0 or count % 2 != 0:
        return False
    half = count // 2
    return all(mirror_change(changes[step]) == changes[step + half] for step in range(half))


def is_double(changes: List[Change]) -> bool:
    """A method that is both palindromic and rotational is called double."""
    return is_palindromic(changes) and is_rotational(changes)


def describe_symmetry(changes: List[Change]) -> str:
    """A word for what symmetry a method has, for putting on a report."""
    if is_double(changes):
        return "double"
    if is_palindromic(changes):
        return "palindromic"
    if is_rotational(changes):
        return "rotational"
    return "asymmetric"


def half_lead_change(changes: List[Change]) -> Optional[Change]:
    """The change at the half lead, where there is a sensible one to name."""
    count = len(changes)
    if count == 0 or count % 2 != 0:
        return None
    return changes[count // 2 - 1]


def symmetric_notation(changes: List[Change]) -> Tuple[List[Change], List[Change]] | None:
    """Split a palindromic lead into the half and the lead end after the comma.

    Returns None where the method cannot be written that way, which is the
    honest answer for a hybrid rather than forcing a split that loses rows.
    """
    count = len(changes)
    if count < 2:
        return None
    body = changes[:-1]
    if body != list(reversed(body)):
        return None
    half = body[: (len(body) + 1) // 2]
    return half, [changes[-1]]
