"""Turning one method into another, which is how most of them came about.

There are tens of thousands of named methods and almost none of them were
invented from nothing. Somebody took one that existed and reversed it, or
turned it upside down, or rang it with a different lead end, and if the result
was any good it got a name. Cambridge and Primrose differ in one place at the
half lead.

The three that matter are reversing the notation, turning it over so the front
becomes the back, and rotating it, which is both at once. All three are
mechanical operations on the notation, and two things about them are worth
knowing before using them.

Reversing a palindromic method gives back the same method. Nearly everything
that gets rung is palindromic, so that is the usual answer and it is a useful
check rather than a disappointment: if the reverse of a method is not itself,
the method is asymmetric.

Turning a method over moves the work as well as the places. The bell that used
to dodge its way up from the front now does it from the back, so the treble in
the result is doing what the tenor used to, and the classifier will say so.
That is what the operation means; it is not the same as the Reverse in a method
name, which usually reverses about a different point.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from blueline.core.method import Method
from blueline.core.notation import Change, format_notation
from blueline.core.symmetry import mirror_change


def reversed_notation(changes: Tuple[Change, ...]) -> List[Change]:
    """The lead rung backwards, ending where it started.

    The lead end change stays where it is. Everything before it turns round,
    which is what a ringer means by ringing a method backwards.
    """
    if not changes:
        return []
    body = list(changes[:-1])
    return [*reversed(body), changes[-1]]


def mirrored_notation(changes: Tuple[Change, ...]) -> List[Change]:
    """The lead turned upside down, so seconds becomes the back place."""
    return [mirror_change(change) for change in changes]


def rotated_notation(changes: Tuple[Change, ...]) -> List[Change]:
    """Reversed and turned over at once, which is the double of a method."""
    return mirrored_notation(tuple(reversed_notation(changes)))


def reverse_of(method: Method, name: Optional[str] = None) -> Method:
    """The method rung backwards, named Reverse something by convention."""
    return Method(
        name=name or f"Reverse {method.name}",
        stage=method.stage,
        changes=tuple(reversed_notation(method.changes)),
    )


def mirror_of(method: Method, name: Optional[str] = None) -> Method:
    return Method(
        name=name or f"Mirror {method.name}",
        stage=method.stage,
        changes=tuple(mirrored_notation(method.changes)),
    )


def rotation_of(method: Method, name: Optional[str] = None) -> Method:
    return Method(
        name=name or f"Double {method.name}",
        stage=method.stage,
        changes=tuple(rotated_notation(method.changes)),
    )


def with_lead_end(method: Method, notation: str, name: Optional[str] = None) -> Method:
    """The same method with a different change at the lead end.

    Swapping seconds place for the back place turns a whole family of methods
    into another one, which is why so many come in pairs.
    """
    from blueline.core.notation import parse_change

    replacement = parse_change(notation, method.stage)
    return Method(
        name=name or method.name,
        stage=method.stage,
        changes=(*method.changes[:-1], replacement),
    )


def is_same_method(first: Method, second: Method) -> bool:
    """Whether two methods have the same notation at the same stage."""
    return first.stage == second.stage and first.changes == second.changes


def describe_relation(first: Method, second: Method) -> Optional[str]:
    """How two methods are related, if they are.

    Checked in order of how much a ringer would notice. Being the same method
    comes first, then the reverse, because a method that is its own reverse is
    better described as itself.
    """
    if first.stage != second.stage:
        return None
    if is_same_method(first, second):
        return "the same method"
    if second.changes == tuple(reversed_notation(first.changes)):
        return "the reverse"
    if second.changes == tuple(mirrored_notation(first.changes)):
        return "turned over"
    if second.changes == tuple(rotated_notation(first.changes)):
        return "the double"
    if first.changes[:-1] == second.changes[:-1]:
        old = format_notation([first.changes[-1]])
        new = format_notation([second.changes[-1]])
        return f"the same but for {old} against {new} at the lead end"
    return None
