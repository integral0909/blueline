"""Fetching the thing a service was asked about.

Twenty five places were doing the same four lines: find the row, and if it is
not there return a not-found carrying the same sentence. Two of them spelled
the sentence differently, which meant a client matching on the message got a
different answer depending on which endpoint refused it.

Each of these gives back either the row or a failed Result, so the caller
writes one check instead of three lines. They do not wrap the answer in a view:
what a service does with the row afterwards is the service's business, and a
lookup that also decided the shape would be two jobs.
"""

from __future__ import annotations

from blueline.core.method import Method
from blueline.db.models import StoredMethod, StoredRinger, StoredTower
from blueline.db.repositories import (
    MethodRepository,
    RingerRepository,
    TowerRepository,
    to_method,
)
from blueline.service.results import Result, not_found, succeeded


def stored_method(methods: MethodRepository, title: str) -> Result[StoredMethod]:
    """The stored row for a title."""
    found = methods.find(title)
    if found is None:
        return not_found(f"no method called {title!r}")
    return succeeded(found)


def method_of(methods: MethodRepository, title: str) -> Result[Method]:
    """The method itself, for a caller that does not need the row.

    Most of them do not. They want the notation rebuilt into a Method and
    nothing else out of the row.
    """
    found = stored_method(methods, title)
    if not found.ok:
        return Result(failure=found.failure)
    return succeeded(to_method(found.unwrap()))


def stored_ringer(ringers: RingerRepository, name: str) -> Result[StoredRinger]:
    found = ringers.find(name)
    if found is None:
        return not_found(f"no ringer called {name!r}")
    return succeeded(found)


def stored_tower(towers: TowerRepository, place: str) -> Result[StoredTower]:
    found = towers.find(place)
    if found is None:
        return not_found(f"no tower at {place!r}")
    return succeeded(found)
