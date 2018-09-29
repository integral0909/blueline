"""Looking for callings, either any true one or one at a length."""

from __future__ import annotations

from typing import Optional, Tuple

from dataclasses import dataclass

from blueline.core.method import Method
from blueline.core.quarters import Target, find_for, reachable
from blueline.core.search import Found, Limits, search_callings
from blueline.db.repository import MethodRepository, to_method
from blueline.service.proving import calls_for
from blueline.service.results import Result, invalid, not_found, succeeded


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
    stored = repository.find(title)
    if stored is None:
        return not_found(f"no method called {title!r}")
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
    stored = repository.find(title)
    if stored is None:
        return not_found(f"no method called {title!r}")
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
