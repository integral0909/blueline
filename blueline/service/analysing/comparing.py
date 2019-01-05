"""Comparing one method against another."""

from __future__ import annotations

from typing import Tuple

from dataclasses import dataclass

from blueline.core.compare import CompareError, compare, most_alike, shared_work
from blueline.db.repositories import MethodRepository, to_method
from blueline.service.lookups import stored_method
from blueline.service.results import Result, invalid, not_found, succeeded


@dataclass(frozen=True)
class ComparisonView:
    """Two methods, side by side."""

    left: str
    right: str
    changes: int
    same: int
    share: float
    same_lead_head: bool
    same_length: bool
    identical: bool
    divergences: Tuple[str, ...]
    work: Tuple[Tuple[int, int], ...]
    summary: str


def compare_methods(
    repository: MethodRepository,
    left: str,
    right: str,
) -> Result[ComparisonView]:
    """How alike two stored methods are."""
    looked_up = stored_method(repository, left)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    one = looked_up.unwrap()
    looked_up = stored_method(repository, right)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    other = looked_up.unwrap()

    first, second = to_method(one), to_method(other)
    try:
        result = compare(first, second)
    except CompareError as error:
        return invalid(str(error))

    return succeeded(
        ComparisonView(
            left=one.title,
            right=other.title,
            changes=result.changes,
            same=result.same,
            share=result.share,
            same_lead_head=result.same_lead_head,
            same_length=result.same_length,
            identical=result.identical,
            divergences=tuple(str(each) for each in result.divergences),
            work=tuple(
                (bell, shared_work(first, second, bell)) for bell in range(1, first.stage + 1)
            ),
            summary=result.summary(),
        )
    )


def nearest_to(repository: MethodRepository, title: str) -> Result[ComparisonView]:
    """Whichever stored method a method is most like.

    What a teacher reaches for: this is nearly Yorkshire, ring it like that and
    watch the back work.
    """
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()

    wanted = to_method(stored)
    among = [to_method(row) for row in repository.search(stage=wanted.stage)]
    nearest = most_alike(wanted, among)
    if nearest is None:
        return not_found(f"nothing else at {wanted.stage} to compare {stored.title} against")

    for row in repository.search(stage=wanted.stage):
        if to_method(row).changes == nearest.changes:
            return compare_methods(repository, stored.title, row.title)
    return not_found("the nearest method went missing between two queries")
