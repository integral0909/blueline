"""Ringers, and what a tower knows about them.

A band is a list of names on a peal board. A ringer is a person who turns up
on Tuesdays, can ring some methods and not others, and is learning one more.
Keeping the two apart matters because the questions are different: a peal board
wants names in bell order, and a tower captain wants to know who can ring
Cambridge before deciding what to put on.

What a ringer can ring is kept as a set of titles rather than anything cleverer.
A tower captain knows perfectly well who can ring what, and a system that tried
to infer it from performances would be wrong about everybody who has just
learnt something.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List

from dataclasses import dataclass, field

from blueline.core.titles import fold
from blueline.errors import BluelineError


class RingerError(BluelineError):
    """A ringer who cannot be described."""


@dataclass(frozen=True)
class Ringer:
    """Somebody who rings, and what they can ring."""

    name: str
    can_ring: FrozenSet[str] = field(default_factory=frozenset)
    learning: FrozenSet[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise RingerError("a ringer has to have a name")
        both = self.can_ring & self.learning
        if both:
            raise RingerError(f"{self.name} cannot be both ringing and learning {sorted(both)[0]}")

    def rings(self, title: str) -> bool:
        return fold(title) in {fold(each) for each in self.can_ring}

    def is_learning(self, title: str) -> bool:
        return fold(title) in {fold(each) for each in self.learning}

    def knows_anything_of(self, title: str) -> bool:
        return self.rings(title) or self.is_learning(title)

    def learnt(self, title: str) -> Ringer:
        """The same ringer, having got a method under their belt."""
        return Ringer(
            name=self.name,
            can_ring=self.can_ring | {title},
            learning=frozenset(each for each in self.learning if fold(each) != fold(title)),
        )

    def __str__(self) -> str:
        return f"{self.name} ({len(self.can_ring)} methods)"


def who_can_ring(ringers: List[Ringer], title: str) -> List[str]:
    """Everybody who can ring a method, in name order."""
    return sorted(ringer.name for ringer in ringers if ringer.rings(title))


def who_is_learning(ringers: List[Ringer], title: str) -> List[str]:
    return sorted(ringer.name for ringer in ringers if ringer.is_learning(title))


def enough_for(ringers: List[Ringer], title: str, stage: int) -> bool:
    """Whether enough people can ring a method to get it off the ground.

    Everybody but one has to know it. A band will carry one person who is
    learning and will not carry two, which is the rule every tower captain
    works to whether or not they would put it that way.
    """
    able = sum(1 for ringer in ringers if ringer.rings(title))
    return able >= stage - 1 and len(ringers) >= stage


def what_the_band_can_ring(ringers: List[Ringer], titles: List[str], stage: int) -> List[str]:
    """Which of the methods this band could actually get through."""
    return sorted(title for title in titles if enough_for(ringers, title, stage))


def learning_together(ringers: List[Ringer]) -> Dict[str, List[str]]:
    """What people are learning, and who else is learning it.

    A tower captain putting on a practice wants the method two people are
    working on, not the one somebody mentioned once.
    """
    found: Dict[str, List[str]] = {}
    for ringer in ringers:
        for title in ringer.learning:
            found.setdefault(title, []).append(ringer.name)
    return {title: sorted(names) for title, names in sorted(found.items())}
