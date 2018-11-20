"""Named sets of methods, which is how bands actually talk about them.

Nobody says "we ring Cambridge, Yorkshire, Superlative, Lincolnshire, London,
Bristol, Rutland and Pudsey". They say "we ring the standard eight". A tower
has a repertoire, a district has a set for its striking competition, and a band
learning spliced works through a named group one method at a time.

A collection is a set rather than a list. The order methods get taught in is a
property of how hard they are, which core.learning already works out, and a
stored order would go out of date the moment somebody added one in the middle.

Nothing here holds methods, only their titles. A collection outlives whatever
happens to be in the library: a tower that has not entered Bristol yet still
rings the standard eight, and a set that silently shrank to whatever was stored
would be a set that meant nothing.
"""

from __future__ import annotations

from typing import FrozenSet, Set, Tuple

from dataclasses import dataclass, field

from blueline.errors import BluelineError

#: Nothing anybody would call a set. Past this it is a library.
MOST_TITLES = 200


class CollectionError(BluelineError):
    """A collection that does not make sense."""


def fold(title: str) -> str:
    """A title as it compares, which is not how it prints."""
    return " ".join(title.strip().lower().split())


@dataclass(frozen=True)
class Collection:
    """A named set of methods."""

    name: str
    titles: FrozenSet[str] = field(default_factory=frozenset)
    note: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise CollectionError("a collection needs a name")
        if len(self.titles) > MOST_TITLES:
            raise CollectionError(f"a collection of {len(self.titles)} is a library")
        cleaned = [title.strip() for title in self.titles]
        if any(not title for title in cleaned):
            raise CollectionError("a collection cannot hold a blank title")
        folded = [fold(title) for title in cleaned]
        if len(set(folded)) != len(folded):
            raise CollectionError("a method cannot be in a collection twice")

    def __len__(self) -> int:
        return len(self.titles)

    def __contains__(self, title: object) -> bool:
        if not isinstance(title, str):
            return False
        return fold(title) in {fold(each) for each in self.titles}

    @property
    def sorted(self) -> Tuple[str, ...]:
        """The titles in name order, which is how a list of them prints."""
        return tuple(sorted(self.titles, key=fold))

    def with_added(self, title: str) -> Collection:
        if title in self:
            raise CollectionError(f"{title} is already in {self.name}")
        return Collection(
            name=self.name,
            titles=self.titles | {title.strip()},
            note=self.note,
        )

    def without(self, title: str) -> Collection:
        if title not in self:
            raise CollectionError(f"{title} is not in {self.name}")
        wanted = fold(title)
        return Collection(
            name=self.name,
            titles=frozenset(each for each in self.titles if fold(each) != wanted),
            note=self.note,
        )

    def summary(self) -> str:
        if not self.titles:
            return f"{self.name}, empty"
        return f"{self.name}, {len(self.titles)} methods"


def overlap(first: Collection, second: Collection) -> FrozenSet[str]:
    """What two collections have in common, as the first one spells them."""
    shared = {fold(title) for title in second.titles}
    return frozenset(title for title in first.titles if fold(title) in shared)


def missing_from(collection: Collection, known: Set[str]) -> FrozenSet[str]:
    """What is in a collection that somebody does not ring."""
    folded = {fold(title) for title in known}
    return frozenset(title for title in collection.titles if fold(title) not in folded)


def covered_by(collection: Collection, known: Set[str]) -> float:
    """How much of a collection somebody rings, as a share.

    An empty collection is fully covered rather than a division by zero. A
    band that rings nothing has still rung all of nothing.
    """
    if not collection.titles:
        return 1.0
    left = len(missing_from(collection, known))
    return (len(collection) - left) / len(collection)


#: The sets everybody means when they name one. Held as titles rather than as
#: methods for the same reason a stored collection is: the standard eight is
#: eight methods whether or not this library happens to hold Pudsey.
STANDARD_EIGHT = Collection(
    name="the standard eight",
    titles=frozenset(
        {
            "Cambridge Surprise Major",
            "Yorkshire Surprise Major",
            "Superlative Surprise Major",
            "Lincolnshire Surprise Major",
            "London Surprise Major",
            "Bristol Surprise Major",
            "Rutland Surprise Major",
            "Pudsey Surprise Major",
        }
    ),
    note="What a band means by spliced Surprise Major without saying more.",
)

STANDARD_FOUR = Collection(
    name="the standard four",
    titles=frozenset(
        {
            "Cambridge Surprise Major",
            "Yorkshire Surprise Major",
            "Superlative Surprise Major",
            "Rutland Surprise Major",
        }
    ),
    note="The four that all have the same lead heads, so they splice freely.",
)

TREBLE_DODGING_MINOR = Collection(
    name="the standard minor",
    titles=frozenset(
        {
            "Cambridge Surprise Minor",
            "Beverley Surprise Minor",
            "Surfleet Surprise Minor",
            "Norwich Surprise Minor",
            "Ipswich Surprise Minor",
            "Primrose Surprise Minor",
        }
    ),
    note="A common six for a band starting on Surprise Minor.",
)

KNOWN = {
    fold(collection.name): collection
    for collection in (STANDARD_EIGHT, STANDARD_FOUR, TREBLE_DODGING_MINOR)
}


def known(name: str) -> Collection:
    """One of the sets everybody means."""
    wanted = fold(name)
    if wanted not in KNOWN:
        raise CollectionError(f"nothing called {name!r} is a set anybody names")
    return KNOWN[wanted]
