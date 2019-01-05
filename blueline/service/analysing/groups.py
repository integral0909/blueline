"""Which methods take each other's compositions."""

from __future__ import annotations

from typing import List, Optional

from blueline.core.leadheads import group_methods, group_of, share_lead_heads
from blueline.db.repositories import MethodRepository, to_method
from blueline.service.lookups import stored_method
from blueline.service.method_views import GroupView
from blueline.service.results import Result, succeeded


def lead_head_groups(
    repository: MethodRepository,
    stage: Optional[int] = None,
) -> Result[List[GroupView]]:
    """The stored methods sorted into groups that take the same compositions."""
    stored = repository.search(stage=stage)
    methods = [to_method(each) for each in stored]
    by_head = group_methods(methods)

    views: List[GroupView] = []
    for head, titles in by_head.items():
        example = next(m for m in methods if str(m.lead_head) == head)
        group = group_of(example)
        views.append(
            GroupView(
                head=head,
                order=group.order,
                places_at_lead_end=group.places_at_lead_end,
                titles=tuple(titles),
            )
        )
    return succeeded(views)


def takes_the_same_compositions(
    repository: MethodRepository,
    title: str,
) -> Result[List[str]]:
    """Every other stored method a composition for this one would ring to."""
    looked_up = stored_method(repository, title)
    if not looked_up.ok:
        return Result(failure=looked_up.failure)
    stored = looked_up.unwrap()
    method = to_method(stored)
    found = [
        f"{other.name} {other.stage}"
        for other in (to_method(each) for each in repository.all())
        if share_lead_heads(method, other) and other.changes != method.changes
    ]
    return succeeded(sorted(found))
