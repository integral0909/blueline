"""What a band can do with a named set of methods.

Keeping one is the easy half. The useful half is the questions a band asks of
it: how much of this do we ring, what is left, how hard is the rest, and do
these actually splice together or have we written down eight methods that
cannot be rung in one touch.

The sets everybody names are here as well as the ones a tower has stored, and
they are answered for the same way. Somebody asking about the standard eight
should not have to enter it first.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from dataclasses import dataclass

from blueline.analysis import analyse
from blueline.core.collections import (
    KNOWN,
    Collection,
    CollectionError,
    covered_by,
    fold,
    missing_from,
)
from blueline.core.learning import Difficulty, difficulty_of, in_order
from blueline.core.spliced import spliceable
from blueline.db.repositories import (
    CollectionRepository,
    MethodRepository,
    RingerRepository,
    to_collection,
    to_method,
)
from blueline.errors import LibraryError
from blueline.service.results import Result, already_exists, invalid, not_found, succeeded


@dataclass(frozen=True)
class CollectionView:
    """A set, and what the library knows about what is in it."""

    name: str
    note: str
    titles: Tuple[str, ...]
    #: What is in the set that the library does not hold. Not an error: a set
    #: is a set of names and the library is a separate thing.
    not_stored: Tuple[str, ...]
    difficulties: Tuple[Difficulty, ...]
    splices: Optional[bool]
    why_not: str

    @property
    def size(self) -> int:
        return len(self.titles)

    @property
    def hardest(self) -> Optional[Difficulty]:
        return self.difficulties[-1] if self.difficulties else None

    def summary(self) -> str:
        if not self.titles:
            return f"{self.name}, empty"
        held = self.size - len(self.not_stored)
        return f"{self.name}, {self.size} methods, {held} in the library"


@dataclass(frozen=True)
class CoverageView:
    """How much of a set a band rings."""

    name: str
    size: int
    rings: int
    share: float
    missing: Tuple[str, ...]

    def summary(self) -> str:
        return f"{self.name}: {self.rings} of {self.size}, {self.share:.0%}"


def _collection(
    collections: CollectionRepository,
    name: str,
) -> Result[Collection]:
    """A stored set, or one of the ones everybody names."""
    stored = collections.find(name)
    if stored is not None:
        return succeeded(to_collection(stored))
    wanted = fold(name)
    if wanted in KNOWN:
        return succeeded(KNOWN[wanted])
    return not_found(f"no collection called {name!r}")


def view_of(collection: Collection, methods: MethodRepository) -> CollectionView:
    held = []
    missing = []
    for title in collection.sorted:
        stored = methods.find(title)
        if stored is None:
            missing.append(title)
        else:
            held.append(stored)

    ranked = in_order(
        [difficulty_of(analyse(to_method(row), name=row.name), to_method(row)) for row in held]
    )

    splices: Optional[bool] = None
    why_not = ""
    if len(held) < 2:
        # One method splices with itself trivially and nought splices with
        # nothing. Saying yes to either would be saying nothing.
        why_not = "too few of these are stored to say"
    else:
        bad = spliceable([to_method(row) for row in held])
        splices = not bad
        if bad:
            # Only the first pair is quoted. A set of eight that does not
            # splice usually has one odd method in it, and listing all seven
            # pairs it fails against buries that.
            first, second = bad[0]
            why_not = f"{first} and {second} have different lead heads"

    return CollectionView(
        name=collection.name,
        note=collection.note,
        titles=collection.sorted,
        not_stored=tuple(missing),
        difficulties=tuple(ranked),
        splices=splices,
        why_not=why_not,
    )


def keep(
    collections: CollectionRepository,
    methods: MethodRepository,
    name: str,
    titles: List[str],
    note: str = "",
) -> Result[CollectionView]:
    """Write a set down."""
    try:
        collection = Collection(name=name, titles=frozenset(titles), note=note)
    except CollectionError as error:
        return invalid(str(error))
    try:
        collections.add(collection)
    except LibraryError as error:
        return already_exists(str(error))
    return succeeded(view_of(collection, methods))


def fetch(
    collections: CollectionRepository,
    methods: MethodRepository,
    name: str,
) -> Result[CollectionView]:
    found = _collection(collections, name)
    if not found.ok:
        return Result(failure=found.failure)
    return succeeded(view_of(found.unwrap(), methods))


def listing(
    collections: CollectionRepository,
    methods: MethodRepository,
    include_known: bool = True,
) -> Result[List[CollectionView]]:
    """Everything stored, and optionally the sets everybody names."""
    sets = collections.sets()
    if include_known:
        stored = {fold(each.name) for each in sets}
        sets += [each for name, each in KNOWN.items() if name not in stored]
    sets.sort(key=lambda each: fold(each.name))
    return succeeded([view_of(each, methods) for each in sets])


def add_to(
    collections: CollectionRepository,
    methods: MethodRepository,
    name: str,
    title: str,
) -> Result[CollectionView]:
    """Put a method into a stored set."""
    stored = collections.find(name)
    if stored is None:
        return not_found(f"no collection called {name!r} is stored")
    try:
        changed = to_collection(stored).with_added(title)
    except CollectionError as error:
        return already_exists(str(error))
    collections.save(changed)
    return succeeded(view_of(changed, methods))


def take_out(
    collections: CollectionRepository,
    methods: MethodRepository,
    name: str,
    title: str,
) -> Result[CollectionView]:
    """Take a method out of a stored set."""
    stored = collections.find(name)
    if stored is None:
        return not_found(f"no collection called {name!r} is stored")
    try:
        changed = to_collection(stored).without(title)
    except CollectionError as error:
        return not_found(str(error))
    collections.save(changed)
    return succeeded(view_of(changed, methods))


def forget(collections: CollectionRepository, name: str) -> Result[str]:
    try:
        collections.remove(name)
    except LibraryError as error:
        return not_found(str(error))
    return succeeded(name)


def coverage(
    collections: CollectionRepository,
    ringers: RingerRepository,
    name: str,
    who: Optional[str] = None,
) -> Result[CoverageView]:
    """How much of a set a ringer, or the whole band, rings."""
    found = _collection(collections, name)
    if not found.ok:
        return Result(failure=found.failure)
    collection = found.unwrap()

    if who is not None:
        ringer = ringers.find(who)
        if ringer is None:
            return not_found(f"no ringer called {who!r}")
        known = {title for title in ringer.can_ring.splitlines() if title.strip()}
        label = f"{collection.name} for {ringer.name}"
    else:
        known = set()
        for each in ringers.all():
            known |= {title for title in each.can_ring.splitlines() if title.strip()}
        label = f"{collection.name} across the band"

    left = missing_from(collection, known)
    return succeeded(
        CoverageView(
            name=label,
            size=len(collection),
            rings=len(collection) - len(left),
            share=covered_by(collection, known),
            missing=tuple(sorted(left, key=fold)),
        )
    )
