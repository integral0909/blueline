"""Drawing a method out: the line, the falseness, the place bells."""

from __future__ import annotations

from typing import List

from blueline.core.falseness import FalseCourseHead, false_course_heads
from blueline.core.handbells import Pair, crossings, standard_pairs, together
from blueline.core.lines import describe_path, marked_grid, place_bell_order
from blueline.core.method import Method
from blueline.core.ropesight import work_of
from blueline.db.repositories import MethodRepository, to_method
from blueline.service.lookups import stored_method
from blueline.service.method_views import HandbellView, LineView
from blueline.service.results import Result, invalid, succeeded


def line(repository: MethodRepository, title: str, bell: int) -> Result[LineView]:
    """One bell's line through a lead of a stored method."""
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    method = to_method(stored)
    if bell < 1 or bell > method.stage:
        return invalid(f"{stored.title} has no bell {bell}")
    path = method.path_of(bell)
    return succeeded(
        LineView(
            bell=bell,
            places=path,
            described=describe_path(path),
            grid=tuple(marked_grid(method.lead_rows(), bell)),
            work=work_of(method, bell),
        )
    )


def falseness(
    repository: MethodRepository, title: str, limit: int = 20
) -> Result[List[FalseCourseHead]]:
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    return succeeded(false_course_heads(to_method(stored))[:limit])


def place_bells(repository: MethodRepository, title: str) -> Result[List[int]]:
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    return succeeded(place_bell_order(to_method(stored)))


def handbells(repository: MethodRepository, title: str) -> Result[List[HandbellView]]:
    """What each pair does, using the pairing nearly everybody uses.

    Adjacent pairs from the treble up. Anything else is a decision a band has
    made and would have to be passed in, and this is the answer to the question
    somebody actually asks first.
    """
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    method = to_method(stored)
    return succeeded([_pair_view(method, pair) for pair in standard_pairs(method.stage)])


def _pair_view(method: Method, pair: Pair) -> HandbellView:
    return HandbellView(
        pair=str(pair),
        bells=pair.bells,
        crossings=tuple(crossings(method, pair)),
        together=tuple(together(method, pair)),
    )
