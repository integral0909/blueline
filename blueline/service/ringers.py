"""Who rings what, taken from what a tower captain types.

Titles come in as a list of strings because that is what a form sends. Nothing
checks them against the library on purpose: a captain entering Bristol Surprise
Major for somebody who can ring it should not be stopped because nobody has put
Bristol in yet.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from dataclasses import dataclass

from blueline.core.ringers import (
    Ringer,
    RingerError,
    enough_for,
    learning_together,
    what_the_band_can_ring,
)
from blueline.db.models import StoredRinger
from blueline.db.repositories import MethodRepository, RingerRepository, to_ringer
from blueline.errors import BluelineError
from blueline.service.lookups import stored_ringer
from blueline.service.results import Result, already_exists, invalid, succeeded


@dataclass(frozen=True)
class RingerView:
    """A ringer as anybody wants to read them."""

    name: str
    can_ring: Tuple[str, ...]
    learning: Tuple[str, ...]

    @property
    def method_count(self) -> int:
        return len(self.can_ring)

    def summary(self) -> str:
        parts = [f"{self.method_count} methods"]
        if self.learning:
            parts.append(f"learning {', '.join(self.learning)}")
        return f"{self.name}: {', '.join(parts)}"


def view_of(stored: StoredRinger) -> RingerView:
    ringer = to_ringer(stored)
    return RingerView(
        name=ringer.name,
        can_ring=tuple(sorted(ringer.can_ring)),
        learning=tuple(sorted(ringer.learning)),
    )


def make_ringer(name: str, can_ring: List[str], learning: List[str]) -> Result[Ringer]:
    try:
        return succeeded(
            Ringer(
                name=name,
                can_ring=frozenset(title.strip() for title in can_ring if title.strip()),
                learning=frozenset(title.strip() for title in learning if title.strip()),
            )
        )
    except BluelineError as error:
        return invalid(str(error))


def add(
    repository: RingerRepository,
    name: str,
    can_ring: Optional[List[str]] = None,
    learning: Optional[List[str]] = None,
) -> Result[RingerView]:
    built = make_ringer(name, can_ring or [], learning or [])
    if not built.ok:
        return Result(failure=built.failure)
    ringer = built.unwrap()
    if repository.find(ringer.name) is not None:
        return already_exists(f"{ringer.name} is already stored")
    return succeeded(view_of(repository.add(ringer)))


def fetch(repository: RingerRepository, name: str) -> Result[RingerView]:
    looked_up = stored_ringer(repository, name)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    return succeeded(view_of(stored))


def remove(repository: RingerRepository, name: str) -> Result[str]:
    looked_up = stored_ringer(repository, name)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    repository.remove(stored.name)
    return succeeded(stored.name)


def everybody(repository: RingerRepository) -> Result[List[RingerView]]:
    return succeeded([view_of(stored) for stored in repository.all()])


def learnt(repository: RingerRepository, name: str, title: str) -> Result[RingerView]:
    """Move a method from what somebody is learning to what they can ring."""
    looked_up = stored_ringer(repository, name)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    if not title.strip():
        return invalid("a method has to be named")
    try:
        updated = to_ringer(stored).learnt(title.strip())
    except RingerError as error:
        return invalid(str(error))
    return succeeded(view_of(repository.save(updated)))


def who_can_ring(repository: RingerRepository, title: str) -> Result[List[str]]:
    """Everybody who can ring a method.

    The query narrows on the stored text and this checks each one properly,
    because a title can sit inside a longer one.
    """
    found = [
        stored.name for stored in repository.who_rings(title) if to_ringer(stored).rings(title)
    ]
    return succeeded(sorted(found))


def what_can_be_rung(
    ringers: RingerRepository,
    methods: MethodRepository,
    stage: int,
) -> Result[List[str]]:
    """Which stored methods this band could actually get through."""
    band = ringers.band()
    if len(band) < stage:
        return invalid(f"{len(band)} ringers is not enough for {stage} bells")
    titles = [stored.title for stored in methods.search(stage=stage)]
    return succeeded(what_the_band_can_ring(band, titles, stage))


def learning(repository: RingerRepository) -> Result[Dict[str, List[str]]]:
    """What people are learning, and who else is learning it."""
    return succeeded(learning_together(repository.band()))


def can_the_band_ring(
    repository: RingerRepository,
    title: str,
    stage: int,
) -> Result[bool]:
    return succeeded(enough_for(repository.band(), title, stage))
