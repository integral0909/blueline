"""Everything about one method, in one answer.

A client showing a method's page wants the analysis, the blue line, the
falseness, the calling positions, what it is like to ring in hand, how hard it
is, and what has been written for it. That is seven calls, and six of them
start by fetching the same row.

So this is one call that does all of it. The pieces are the same functions the
individual endpoints use, called in turn, because two ways of working out a
method's falseness would eventually disagree.

What a caller does not want is included anyway rather than made optional. The
expensive part is proving the compositions, and that is already capped; the
rest is arithmetic on a lead of rows and costs less than the round trip a
second call would take.
"""

from __future__ import annotations

from typing import Tuple

from dataclasses import dataclass

from blueline.analysis import MethodReport, analyse
from blueline.core.falseness import FalseCourseHead
from blueline.core.learning import Difficulty, difficulty_of
from blueline.db.repositories import (
    CollectionRepository,
    CompositionRepository,
    MethodRepository,
    to_collection,
    to_method,
)
from blueline.service.analysing import falseness, handbells, line, place_bells
from blueline.service.calls import PositionView, positions
from blueline.service.compositions import CompositionView, for_method
from blueline.service.lookups import stored_method
from blueline.service.method_views import HandbellView, LineView
from blueline.service.results import Result, invalid, succeeded

#: How many false course heads to bother with. A client showing a page has
#: room for a handful and the full list at major runs to hundreds.
FALSENESS = 12


@dataclass(frozen=True)
class Dossier:
    """Everything about one method."""

    report: MethodReport
    difficulty: Difficulty
    line: LineView
    place_bells: Tuple[int, ...]
    falseness: Tuple[FalseCourseHead, ...]
    handbells: Tuple[HandbellView, ...]
    positions: Tuple[PositionView, ...]
    compositions: Tuple[CompositionView, ...]
    in_sets: Tuple[str, ...]

    @property
    def title(self) -> str:
        return str(self.report.title)

    @property
    def course_is_true(self) -> bool:
        return self.report.course_is_true

    def summary(self) -> str:
        truth = "true" if self.course_is_true else "false"
        return (
            f"{self.title}: {self.report.lead_length} changes to a lead, "
            f"{self.difficulty.band}, plain course {truth}"
        )


def compile_dossier(
    methods: MethodRepository,
    compositions: CompositionRepository,
    collections: CollectionRepository,
    title: str,
    bell: int = 2,
    most_falseness: int = FALSENESS,
) -> Result[Dossier]:
    """Everything about one method, worked out once."""
    if most_falseness < 1:
        return invalid("a dossier has to be allowed to list some falseness")

    looked_up = stored_method(methods, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()

    method = to_method(stored)
    if not 1 <= bell <= method.stage:
        return invalid(f"there is no bell {bell} in a method at {method.stage}")

    drawn = line(methods, stored.title, bell)
    if not drawn.ok:
        return Result(failure=drawn.failure)

    false = falseness(methods, stored.title, limit=most_falseness)
    if not false.ok:
        return Result(failure=false.failure)

    report = analyse(method, name=stored.name)
    held = for_method(compositions, methods, stored.title)
    in_sets = tuple(
        sorted(
            to_collection(row).name
            for row in collections.holding(stored.title)
            if stored.title in to_collection(row)
        )
    )

    return succeeded(
        Dossier(
            report=report,
            difficulty=difficulty_of(report, method),
            line=drawn.unwrap(),
            place_bells=tuple(place_bells(methods, stored.title).unwrap()),
            falseness=tuple(false.unwrap()),
            handbells=tuple(handbells(methods, stored.title).unwrap()),
            positions=tuple(positions(methods, stored.title).unwrap()),
            compositions=tuple(held.unwrap()) if held.ok else (),
            in_sets=in_sets,
        )
    )
