"""Spliced touches, assembled from what somebody typed.

Takes the initials a band would write on a card and turns them into a touch,
having first checked the methods can actually be spliced together. Refusing up
front with the pair that will not go is more use than proving a touch false and
leaving somebody to work out why.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from dataclasses import dataclass

from blueline.core.method import Method
from blueline.core.music import MusicCount
from blueline.core.peals import Standing
from blueline.core.spliced import Spliced, build_spliced, spliceable
from blueline.core.truth import Repeat
from blueline.db.repositories import MethodRepository, to_method
from blueline.errors import BluelineError
from blueline.service.lookups import stored_method
from blueline.service.proving import calls_for
from blueline.service.reports import Outcome, outcome_of
from blueline.service.results import Result, invalid, succeeded


@dataclass(frozen=True)
class SplicedReport:
    """What a spliced touch does."""

    order: str
    calling: str
    methods_used: Tuple[str, ...]
    outcome: Outcome

    @property
    def leads(self) -> int:
        return self.outcome.leads

    @property
    def length(self) -> int:
        return self.outcome.length

    @property
    def comes_round(self) -> bool:
        return self.outcome.comes_round

    @property
    def is_true(self) -> bool:
        return self.outcome.is_true

    @property
    def repeats(self) -> Tuple[Repeat, ...]:
        return self.outcome.repeats

    @property
    def music(self) -> MusicCount:
        return self.outcome.music

    @property
    def final_row(self) -> str:
        return self.outcome.final_row

    @property
    def standing(self) -> Standing:
        return self.outcome.standing

    @property
    def is_ringable(self) -> bool:
        return self.outcome.is_ringable

    def summary(self) -> str:
        used = len(self.methods_used)
        word = "method" if used == 1 else "methods"
        return self.outcome.summarise(f"{used} {word}")


def gather(repository: MethodRepository, titles: List[str]) -> Result[Dict[str, Method]]:
    """Look up the methods a splice needs, keyed by their bare names."""
    found: Dict[str, Method] = {}
    for title in titles:
        looked_up = stored_method(repository, title)
        if not looked_up.ok:
            return Result(failure=looked_up.failure)
        stored = looked_up.unwrap()
        method = to_method(stored)
        if method.name[0].upper() in {name[0].upper() for name in found}:
            return invalid(f"{method.name} and another method share an initial")
        found[method.name] = method
    if not found:
        return invalid("a splice needs at least one method")
    return succeeded(found)


def report_on(touch: Spliced) -> SplicedReport:
    return SplicedReport(
        order=touch.order,
        calling=touch.calling,
        methods_used=tuple(touch.methods_used()),
        outcome=outcome_of(touch.rows(), touch.leads),
    )


def splice(
    repository: MethodRepository,
    titles: List[str],
    order: str,
    calling: str = "",
) -> Result[SplicedReport]:
    """Build and prove a spliced touch."""
    gathered = gather(repository, titles)
    if not gathered.ok:
        return Result(failure=gathered.failure)
    methods = gathered.unwrap()

    stages = {method.stage for method in methods.values()}
    if len(stages) > 1:
        return invalid(f"cannot splice across stages {sorted(stages)}")

    clashes = spliceable(list(methods.values()))
    if clashes:
        first, second = clashes[0]
        return invalid(f"{first} and {second} do not splice, their lead heads differ")

    any_method = next(iter(methods.values()))
    try:
        touch = build_spliced(methods, order, calls_for(any_method), calling)
    except BluelineError as error:
        return invalid(str(error))
    return succeeded(report_on(touch))
