"""Comparing titles, and keeping sets of them.

A title is what somebody typed, and two people type the same method three ways.
Cambridge Surprise Major, cambridge surprise major, and Cambridge  Surprise
Major are one method, and every part of this that holds titles had grown its
own idea of that: two modules with a private fold, two repositories with their
own pair of functions turning a set into text and back.

They are one set of functions now. The rule is: compare folded, store as
written. A tower that types Pudsey Surprise Major gets Pudsey Surprise Major
back, and a search for pudsey finds it.

Titles are stored as lines rather than as rows in a join table wherever they
appear. Nothing joins to a method from a ringer or a collection, because a
band's repertoire is what they call things and not what the library happens to
hold, and a foreign key would refuse half of it.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from collections.abc import Iterable


def fold(title: str) -> str:
    """A title as it compares, which is not how it prints.

    Whitespace is collapsed as well as trimmed. "Cambridge  Surprise Major"
    with two spaces in it comes off a paste as often as anything.
    """
    return " ".join(title.strip().lower().split())


def same_title(one: str, other: str) -> bool:
    return fold(one) == fold(other)


def holds(titles: Iterable[str], wanted: str) -> bool:
    """Whether a set of titles has one in it, however it was typed."""
    folded = fold(wanted)
    return any(fold(title) == folded for title in titles)


def without(titles: Iterable[str], unwanted: str) -> FrozenSet[str]:
    """The set with one taken out, however it was typed."""
    folded = fold(unwanted)
    return frozenset(title for title in titles if fold(title) != folded)


def in_order(titles: Iterable[str]) -> Tuple[str, ...]:
    """Titles as they print, sorted the way they compare."""
    return tuple(sorted(titles, key=fold))


def as_lines(titles: Iterable[str]) -> str:
    """A set of titles as one column of text, for storing."""
    return "\n".join(in_order(titles))


def from_lines(text: str) -> FrozenSet[str]:
    """The titles back out of stored text, blank lines dropped."""
    return frozenset(line.strip() for line in text.splitlines() if line.strip())
