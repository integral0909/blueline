"""Looking over the library for things that have gone wrong.

Data goes bad slowly. Somebody edits a method's notation and the compositions
written for it quietly stop proving. Somebody enters Cambridge twice under two
spellings. A collection names a method that was later removed. None of these
raise anything; they just sit there until somebody rings a false touch.

So this goes and looks. It changes nothing, because a check that repaired
things would be a check nobody dared run, and half of what it finds needs a
person to decide what the right answer was.

Everything is reported at one of two levels. A problem is something that is
wrong and will bite: a composition that no longer comes round. A note is
something worth a look that may be perfectly intentional: two methods with the
same notation under different names is how a variation gets entered.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from dataclasses import dataclass, field

from blueline.analysis import analyse
from blueline.core.titles import fold, from_lines
from blueline.db.repositories import (
    CollectionRepository,
    CompositionRepository,
    MethodRepository,
    RingerRepository,
    to_collection,
    to_method,
)
from blueline.errors import BluelineError
from blueline.service.proving import prove
from blueline.service.results import Result, succeeded

PROBLEM = "problem"
NOTE = "note"


@dataclass(frozen=True)
class Finding:
    """One thing that is wrong, or worth a look."""

    level: str
    subject: str
    detail: str

    @property
    def is_problem(self) -> bool:
        return self.level == PROBLEM

    def __str__(self) -> str:
        return f"{self.level}: {self.subject}: {self.detail}"


@dataclass(frozen=True)
class CheckReport:
    """What looking over the library turned up."""

    checked: int
    findings: Tuple[Finding, ...] = field(default_factory=tuple)

    @property
    def problems(self) -> Tuple[Finding, ...]:
        return tuple(each for each in self.findings if each.is_problem)

    @property
    def notes(self) -> Tuple[Finding, ...]:
        return tuple(each for each in self.findings if not each.is_problem)

    @property
    def clean(self) -> bool:
        return not self.problems

    def summary(self) -> str:
        if not self.findings:
            return f"{self.checked} things checked, nothing to report"
        return (
            f"{self.checked} things checked, {len(self.problems)} problems, "
            f"{len(self.notes)} worth a look"
        )


def _check_methods(methods: MethodRepository) -> List[Finding]:
    found: List[Finding] = []
    by_notation: Dict[Tuple[int, str], List[str]] = {}
    by_title: Dict[str, List[str]] = {}

    for stored in methods.all():
        by_title.setdefault(fold(stored.title), []).append(stored.title)
        try:
            method = to_method(stored)
        except BluelineError as error:
            found.append(Finding(PROBLEM, stored.title, f"will not parse: {error}"))
            continue

        by_notation.setdefault((stored.stage, method.notation), []).append(stored.title)

        report = analyse(method, name=stored.name)
        worked_out = report.classification.kind
        if stored.classification and stored.classification != worked_out:
            found.append(
                Finding(
                    PROBLEM,
                    stored.title,
                    f"stored as {stored.classification} but reads as {worked_out}",
                )
            )
        if str(report.title) != stored.title:
            found.append(
                Finding(NOTE, stored.title, f"the analyser would call this {report.title}")
            )

    for titles in by_title.values():
        if len(titles) > 1:
            found.append(Finding(PROBLEM, titles[0], f"stored {len(titles)} times under one title"))
    for titles in by_notation.values():
        if len(titles) > 1:
            found.append(
                Finding(NOTE, titles[0], f"same notation as {', '.join(sorted(titles[1:]))}")
            )
    return found


def _check_compositions(
    compositions: CompositionRepository,
    methods: MethodRepository,
) -> List[Finding]:
    found: List[Finding] = []
    for stored in compositions.longest(limit=100_000):
        report = prove(methods, stored.method.title, stored.calling)
        if not report.ok:
            assert report.failure is not None
            found.append(Finding(PROBLEM, stored.title, report.failure.detail))
            continue
        proved = report.unwrap()
        if not proved.comes_round:
            found.append(Finding(PROBLEM, stored.title, "no longer comes round"))
        elif proved.is_true != stored.is_true:
            was = "true" if stored.is_true else "false"
            now = "true" if proved.is_true else "false"
            found.append(Finding(PROBLEM, stored.title, f"was {was} and is now {now}"))
        elif proved.length != stored.length:
            found.append(
                Finding(
                    NOTE,
                    stored.title,
                    f"stored as {stored.length} changes and now comes to {proved.length}",
                )
            )
    return found


def _check_collections(
    collections: CollectionRepository,
    methods: MethodRepository,
) -> List[Finding]:
    found: List[Finding] = []
    for stored in collections.all():
        collection = to_collection(stored)
        missing = [title for title in collection.sorted if methods.find(title) is None]
        if missing:
            found.append(
                Finding(
                    NOTE,
                    collection.name,
                    f"names {len(missing)} methods the library does not hold",
                )
            )
        if not collection.titles:
            found.append(Finding(NOTE, collection.name, "is empty"))
    return found


def _check_ringers(ringers: RingerRepository, methods: MethodRepository) -> List[Finding]:
    found: List[Finding] = []
    for stored in ringers.all():
        for title in sorted(from_lines(stored.can_ring), key=fold):
            if methods.find(title) is None:
                found.append(
                    Finding(NOTE, stored.name, f"rings {title}, which is not in the library")
                )
    return found


def check(
    methods: MethodRepository,
    compositions: CompositionRepository,
    collections: CollectionRepository,
    ringers: RingerRepository,
    thorough: bool = False,
) -> Result[CheckReport]:
    """Look over everything stored and say what is wrong.

    The thorough pass proves every stored composition again, which is the
    expensive half and the half that finds the thing that actually matters.
    Off by default so somebody can run this on a big library without waiting.
    """
    findings = _check_methods(methods)
    findings += _check_collections(collections, methods)
    findings += _check_ringers(ringers, methods)
    checked = methods.count() + collections.count() + ringers.count()

    if thorough:
        findings += _check_compositions(compositions, methods)
        checked += compositions.count()

    findings.sort(key=lambda each: (each.level != PROBLEM, each.subject, each.detail))
    return succeeded(CheckReport(checked=checked, findings=tuple(findings)))
