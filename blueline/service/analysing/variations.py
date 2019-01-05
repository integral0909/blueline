"""Turning one method into another: variations, and changed lead ends."""

from __future__ import annotations

from typing import Optional

from blueline.analysis import MethodReport, analyse
from blueline.core.variations import (
    describe_relation,
    mirror_of,
    reverse_of,
    rotation_of,
    with_lead_end,
)
from blueline.db.repositories import MethodRepository, to_method
from blueline.errors import BluelineError
from blueline.service.lookups import stored_method
from blueline.service.results import Result, invalid, succeeded

#: The transforms a caller can ask for, by the word they would use.
VARIATIONS = {
    "reverse": reverse_of,
    "mirror": mirror_of,
    "double": rotation_of,
}


def vary(
    repository: MethodRepository,
    title: str,
    kind: str,
    name: Optional[str] = None,
) -> Result[MethodReport]:
    """Analyse a variation of a stored method without storing it.

    Nothing is written. Somebody trying the reverse of a method wants to know
    whether it is worth having before it goes in the library under a name.
    """
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    make = VARIATIONS.get(kind.strip().lower())
    if make is None:
        known = ", ".join(sorted(VARIATIONS))
        return invalid(f"no such variation as {kind!r}, try one of {known}")
    return succeeded(analyse(make(to_method(stored), name=name)))


def relate(repository: MethodRepository, first: str, second: str) -> Result[str]:
    """How two stored methods are related, in words."""
    looked_up = stored_method(repository, first)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    left = looked_up.unwrap()
    looked_up = stored_method(repository, second)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    right = looked_up.unwrap()
    relation = describe_relation(to_method(left), to_method(right))
    return succeeded(relation or "not related")


def change_lead_end(
    repository: MethodRepository,
    title: str,
    notation: str,
    name: Optional[str] = None,
) -> Result[MethodReport]:
    """Analyse the same method with a different change at the lead end."""
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    try:
        varied = with_lead_end(to_method(stored), notation, name=name)
    except BluelineError as error:
        return invalid(str(error))
    return succeeded(analyse(varied))
