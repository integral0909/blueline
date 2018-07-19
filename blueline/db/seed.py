"""Putting the standard methods into a fresh database.

There used to be a MethodLibrary that held the standard set in memory and knew
how to search it. It was written before anything was stored, and once the
repository existed the two were doing the same job with two different search
implementations that had already started to disagree about whether a name match
was a substring or not.

The standard set is just a list of methods now. Anything that wants to look
through it seeds a database and asks the repository, so there is one search and
one set of rules about what matching means.
"""

from __future__ import annotations

from typing import List, Tuple

from dataclasses import dataclass

from blueline.db.repository import MethodRepository
from blueline.errors import LibraryError
from blueline.library.builtin import standard_methods


@dataclass(frozen=True)
class SeedReport:
    """What seeding did, so a caller can say so rather than guessing."""

    added: Tuple[str, ...]
    skipped: Tuple[str, ...]

    @property
    def total(self) -> int:
        return len(self.added) + len(self.skipped)

    def __str__(self) -> str:
        return f"{len(self.added)} added, {len(self.skipped)} already there"


def seed_standard(repository: MethodRepository, skip_existing: bool = True) -> SeedReport:
    """Load the standard set, leaving alone anything already stored.

    Skipping rather than failing means this can be run against a database
    somebody has already added their own methods to, which is the normal case
    every time the application starts.
    """
    added: List[str] = []
    skipped: List[str] = []
    for method in standard_methods():
        try:
            stored = repository.add(method)
        except LibraryError:
            if not skip_existing:
                raise
            skipped.append(method.name)
            continue
        added.append(stored.title)
    return SeedReport(added=tuple(added), skipped=tuple(skipped))
