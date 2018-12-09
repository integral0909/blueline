"""Looking for callings: any true one, one at a length, or a musical one."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from dataclasses import dataclass

from blueline.core.method import Method
from blueline.core.quarters import Target, find_for, reachable
from blueline.core.scoring import Score, best_of, score_rows
from blueline.core.search import Found, Limits, search_callings
from blueline.db.repositories import MethodRepository, to_method
from blueline.service.lookups import stored_method
from blueline.service.proving import build, calls_for
from blueline.service.results import Result, invalid, succeeded


@dataclass(frozen=True)
class SearchReport:
    """What a search turned up, and whether it got to the end."""

    title: str
    found: Tuple[Found, ...]
    exhausted: bool
    looked_at: str

    def summary(self) -> str:
        count = len(self.found)
        word = "calling" if count == 1 else "callings"
        if self.exhausted:
            return f"{count} {word}, searched to the end"
        return f"{count} {word}, stopped early"


def search(
    repository: MethodRepository,
    title: str,
    min_length: int = 1,
    max_length: int = 5040,
    max_found: int = 20,
    allowed: Optional[str] = None,
) -> Result[SearchReport]:
    """Look for callings of a stored method that come round and are true."""
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    if min_length > max_length:
        return invalid(f"{min_length} is longer than the {max_length} asked for")
    if max_found < 1:
        return invalid("a search has to be allowed to find something")

    method = to_method(stored)
    calls = calls_for(method)
    if allowed:
        unknown = [symbol for symbol in allowed if symbol != "p" and symbol not in calls]
        if unknown:
            return invalid(f"{stored.title} has no call written {unknown[0]!r}")

    found, exhausted = search_callings(
        method,
        calls,
        Limits(min_length=min_length, max_length=max_length, max_found=max_found),
        allowed=allowed,
    )
    return succeeded(
        SearchReport(
            title=stored.title,
            found=tuple(found),
            exhausted=exhausted,
            looked_at=allowed or "".join(sorted({"p", *calls})),
        )
    )


@dataclass(frozen=True)
class TargetReport:
    """What looking for a particular length turned up."""

    title: str
    target: str
    wanted: int
    reachable: bool
    why_not: Optional[str]
    found: Tuple[Found, ...]
    exhausted: bool

    def summary(self) -> str:
        if not self.reachable:
            return f"{self.wanted} cannot be rung of this method: {self.why_not}"
        count = len(self.found)
        word = "calling" if count == 1 else "callings"
        tail = "" if self.exhausted else ", stopped early"
        return f"{count} {word} of {self.target}{tail}"


def _why_unreachable(method: Method, target: Target) -> str:
    """Which of the two rules ruled it out, in words."""
    from blueline.core.truth import extent_length

    extent = extent_length(method.stage)
    if target.shortest > extent:
        return f"an extent at this stage is only {extent} rows"
    return f"{method.lead_length} changes to a lead does not divide into it"


def for_length(
    repository: MethodRepository,
    title: str,
    length: int,
    tolerance: int = 0,
    max_found: int = 10,
    allowed: Optional[str] = None,
) -> Result[TargetReport]:
    """Look for callings that come round true at a particular length."""
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    try:
        target = Target(length=length, tolerance=tolerance)
    except ValueError as error:
        return invalid(str(error))
    if max_found < 1:
        return invalid("a search has to be allowed to find something")

    method = to_method(stored)
    calls = calls_for(method)
    if allowed:
        unknown = [symbol for symbol in allowed if symbol != "p" and symbol not in calls]
        if unknown:
            return invalid(f"{stored.title} has no call written {unknown[0]!r}")

    if not reachable(method, target):
        return succeeded(
            TargetReport(
                title=stored.title,
                target=str(target),
                wanted=length,
                reachable=False,
                why_not=_why_unreachable(method, target),
                found=(),
                exhausted=True,
            )
        )

    found, exhausted = find_for(method, calls, target, max_found=max_found, allowed=allowed)
    return succeeded(
        TargetReport(
            title=stored.title,
            target=str(target),
            wanted=length,
            reachable=True,
            why_not=None,
            found=tuple(found),
            exhausted=exhausted,
        )
    )


@dataclass(frozen=True)
class Ranked:
    """One calling, with what it comes to and how musical it is."""

    calling: str
    leads: int
    length: int
    score: float
    per_row: float
    music: str

    def __str__(self) -> str:
        return f"{self.calling} ({self.length}), {self.score:.0f}"


@dataclass(frozen=True)
class MusicReport:
    """The most musical of what a search turned up."""

    title: str
    considered: int
    exhausted: bool
    best: Tuple[Ranked, ...]

    def summary(self) -> str:
        if not self.best:
            return f"{self.title}: nothing came round"
        end = "searched to the end" if self.exhausted else "stopped early"
        return f"{self.title}: {self.considered} callings tried, {end}"


def most_musical(
    repository: MethodRepository,
    title: str,
    min_length: int = 1,
    max_length: int = 5040,
    max_found: int = 200,
    how_many: int = 10,
    allowed: Optional[str] = None,
    min_run: int = 4,
) -> Result[MusicReport]:
    """Search, then rank what came back on its music.

    Two passes rather than one. Scoring inside the search would mean ringing
    every branch through before knowing whether it comes round, and the whole
    reason the search finishes at all is that it drops branches early.

    That does mean what gets ranked is only what the search found, which is
    capped. A wider cap costs time and is the caller's decision, so it is a
    parameter rather than a number in here.
    """
    if how_many < 1:
        return invalid("a ranking has to be allowed to hold something")

    searched = search(
        repository,
        title,
        min_length=min_length,
        max_length=max_length,
        max_found=max_found,
        allowed=allowed,
    )
    if not searched.ok:
        return Result(failure=searched.failure)
    report = searched.unwrap()

    stored = repository.find(title)
    assert stored is not None
    method = to_method(stored)

    scored: List[Tuple[str, Score]] = []
    keeping: Dict[str, Found] = {}
    for each in report.found:
        built = build(method, each.calling)
        if not built.ok:
            # The search produced it, so it parses. Skipping rather than
            # raising keeps one odd calling from losing the whole ranking.
            continue
        scored.append((each.calling, score_rows(built.unwrap().rows(), min_run=min_run)))
        keeping[each.calling] = each

    best = []
    for calling, score in best_of(scored, how_many):
        entry = keeping[calling]
        best.append(
            Ranked(
                calling=calling,
                leads=entry.leads,
                length=entry.length,
                score=round(score.total, 1),
                per_row=round(score.per_row, 4),
                music=score.summary(),
            )
        )

    return succeeded(
        MusicReport(
            title=report.title,
            considered=len(report.found),
            exhausted=report.exhausted,
            best=tuple(best),
        )
    )
