"""Keeping the touches somebody has written down.

A composition is a calling against a method, with a name and usually a
composer. The library has held them since the beginning and nothing has ever
been able to put one in, which is the wrong way round: proving a touch and then
losing it is what a scrap of paper is for.

Everything is proved on the way in. A stored composition that has never been
rung through is a claim, and a library full of claims is worse than an empty
one. What comes back out is proved again rather than trusted, because the
method it points at can be edited underneath it and a composition is only true
of the notation it was proved against.
"""

from __future__ import annotations

from typing import List

from dataclasses import dataclass

from blueline.db.models import StoredComposition
from blueline.db.repositories import (
    CompositionRepository,
    MethodRepository,
)
from blueline.service.proving import TouchReport, prove
from blueline.service.results import Result, invalid, not_found, succeeded

#: Longest name anybody gives a touch. "5040 Plain Bob Triples, arranged from
#: a peal by the late J Reeves" is on the long side and still fits.
LONGEST_TITLE = 120


@dataclass(frozen=True)
class CompositionView:
    """A stored composition, proved again on the way out."""

    id: int
    title: str
    method: str
    composer: str
    calling: str
    length: int
    leads: int
    is_true: bool
    comes_round: bool
    stored_as_true: bool

    @property
    def still_true(self) -> bool:
        """Whether it proves the same way it did when it went in.

        False means the method was edited after the composition was stored.
        Worth saying loudly: a peal composition that quietly became false is
        the sort of thing that gets found out on the day.
        """
        return self.is_true == self.stored_as_true

    def summary(self) -> str:
        truth = "true" if self.is_true else "false"
        return f"{self.title}, {self.length} {truth}"


def _view(stored: StoredComposition, report: TouchReport) -> CompositionView:
    return CompositionView(
        id=stored.id,
        title=stored.title,
        method=stored.method.title,
        composer=stored.composer or "",
        calling=stored.calling,
        length=report.length,
        leads=report.leads,
        is_true=report.is_true,
        comes_round=report.comes_round,
        stored_as_true=stored.is_true,
    )


def _reprove(
    methods: MethodRepository,
    stored: StoredComposition,
) -> Result[CompositionView]:
    report = prove(methods, stored.method.title, stored.calling)
    if not report.ok:
        assert report.failure is not None
        return invalid(f"{stored.title}: {report.failure.detail}")
    return succeeded(_view(stored, report.unwrap()))


def store(
    compositions: CompositionRepository,
    methods: MethodRepository,
    title: str,
    method_title: str,
    calling: str,
    composer: str = "",
) -> Result[CompositionView]:
    """Prove a touch and keep it."""
    name = title.strip()
    if not name:
        return invalid("a composition needs a title")
    if len(name) > LONGEST_TITLE:
        return invalid(f"a title is at most {LONGEST_TITLE} characters")

    stored_method = methods.find(method_title)
    if stored_method is None:
        return not_found(f"no method called {method_title!r}")

    report = prove(methods, stored_method.title, calling)
    if not report.ok:
        return Result(failure=report.failure)
    proved = report.unwrap()
    if not proved.comes_round:
        # Refused rather than stored with a note. A calling that does not come
        # round is a mistake in the calling, not a composition with a flaw.
        return invalid(f"{proved.final_row} is not rounds, so that is not a touch")

    kept = compositions.add(
        method=stored_method,
        title=name,
        calling=calling.strip(),
        length=proved.length,
        is_true=proved.is_true,
        composer=composer.strip() or None,
    )
    return succeeded(_view(kept, proved))


def fetch(
    compositions: CompositionRepository,
    methods: MethodRepository,
    composition_id: int,
) -> Result[CompositionView]:
    stored = compositions.get_by_id(composition_id)
    if stored is None:
        return not_found(f"no composition number {composition_id}")
    return _reprove(methods, stored)


def for_method(
    compositions: CompositionRepository,
    methods: MethodRepository,
    method_title: str,
) -> Result[List[CompositionView]]:
    """Everything written for one method, longest first."""
    stored_method = methods.find(method_title)
    if stored_method is None:
        return not_found(f"no method called {method_title!r}")

    views: List[CompositionView] = []
    for stored in compositions.for_method(stored_method):
        proved = _reprove(methods, stored)
        if proved.ok:
            views.append(proved.unwrap())
    return succeeded(views)


def longest(
    compositions: CompositionRepository,
    methods: MethodRepository,
    limit: int = 10,
) -> Result[List[CompositionView]]:
    """The longest touches in the library, whatever they are of."""
    if limit < 1:
        return invalid(f"cannot list {limit} compositions")
    views: List[CompositionView] = []
    for stored in compositions.longest(limit):
        proved = _reprove(methods, stored)
        if proved.ok:
            views.append(proved.unwrap())
    return succeeded(views)


def remove(compositions: CompositionRepository, composition_id: int) -> Result[int]:
    stored = compositions.get_by_id(composition_id)
    if stored is None:
        return not_found(f"no composition number {composition_id}")
    compositions.delete_row(stored)
    return succeeded(composition_id)
