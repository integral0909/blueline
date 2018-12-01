"""Advice for a ringer, and for whoever is teaching them.

Two questions. What is this method going to ask of me, which is answered for
anything in the library whether anybody has ever rung it or not. And what
should I learn next, which needs to know what the ringer already rings and so
goes through the ringers table.

The advice is about methods, not about people. A ringer who wants Bristol
first is welcome to it and this will still say Cambridge is the easier one.
"""

from __future__ import annotations

from typing import List, Optional, Set, Tuple

from dataclasses import dataclass

from blueline.analysis import analyse
from blueline.core.learning import Difficulty, difficulty_of, in_order, next_after, step_up
from blueline.core.titles import from_lines
from blueline.db.repositories import MethodRepository, RingerRepository, to_method
from blueline.service.results import Result, invalid, not_found, succeeded

#: How many suggestions anybody wants at once. More than a handful is a
#: reading list rather than advice.
MOST_SUGGESTIONS = 10


@dataclass(frozen=True)
class AdviceView:
    """What a ringer should do next."""

    ringer: str
    knows: int
    fill_gaps: Tuple[Difficulty, ...]
    step_up: Optional[Difficulty]

    def summary(self) -> str:
        if self.step_up is None and not self.fill_gaps:
            return f"{self.ringer} rings everything in the library"
        if self.step_up is None:
            return f"{self.ringer} has gaps behind them but nothing new above"
        return f"{self.ringer} could go on to {self.step_up.title}"


def _everything(methods: MethodRepository) -> List[Difficulty]:
    return [
        difficulty_of(analyse(to_method(stored)), to_method(stored)) for stored in methods.all()
    ]


def rank(methods: MethodRepository, stage: Optional[int] = None) -> Result[List[Difficulty]]:
    """The library in order of how hard it is."""
    stored = methods.search(stage=stage) if stage is not None else methods.all()
    if not stored:
        return succeeded([])
    ranked = [difficulty_of(analyse(to_method(row)), to_method(row)) for row in stored]
    return succeeded(in_order(ranked))


def how_hard(methods: MethodRepository, title: str) -> Result[Difficulty]:
    """What one method is going to ask of somebody."""
    stored = methods.find(title)
    if stored is None:
        return not_found(f"no method called {title!r}")
    method = to_method(stored)
    return succeeded(difficulty_of(analyse(method, name=stored.name), method))


def advise(
    methods: MethodRepository,
    ringers: RingerRepository,
    name: str,
    how_many: int = 3,
) -> Result[AdviceView]:
    """What a particular ringer should learn next."""
    if not 1 <= how_many <= MOST_SUGGESTIONS:
        return invalid(f"between 1 and {MOST_SUGGESTIONS} suggestions, not {how_many}")

    stored = ringers.find(name)
    if stored is None:
        return not_found(f"no ringer called {name!r}")

    knows = set(from_lines(stored.can_ring))
    everything = _everything(methods)
    return succeeded(
        AdviceView(
            ringer=stored.name,
            knows=len(knows),
            fill_gaps=tuple(next_after(everything, knows, how_many)),
            step_up=step_up(everything, knows),
        )
    )


def advise_a_band(
    methods: MethodRepository,
    ringers: RingerRepository,
    how_many: int = 3,
) -> Result[List[Difficulty]]:
    """What the whole band could learn together.

    Only what nobody rings yet. A method half the band already has is not
    something to teach on a practice night; it is something to ring.
    """
    if not 1 <= how_many <= MOST_SUGGESTIONS:
        return invalid(f"between 1 and {MOST_SUGGESTIONS} suggestions, not {how_many}")

    everybody = ringers.all()
    if not everybody:
        return not_found("nobody is on the books")

    known: Set[str] = set()
    for stored in everybody:
        known |= set(from_lines(stored.can_ring))
    return succeeded(next_after(_everything(methods), known, how_many))
