"""What every group of commands needs.

The repositories come as a set on one session. Handing each command its own
session looked tidy and was not: a tower fetched through one and attached to a
performance built through another is attached to the wrong session, and
sqlalchemy refuses it. Anything that touches two tables at once needs them to
be looking at the same transaction, which most of these commands do.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TypeVar

from sqlalchemy.orm import Session

from blueline.api.deps import get_factory
from blueline.cli.declare import RED, Exit, secho
from blueline.db.repositories import (
    CollectionRepository,
    CompetitionRepository,
    CompositionRepository,
    MethodRepository,
    PerformanceRepository,
    RingerRepository,
    TowerRepository,
)
from blueline.service.results import Reason, Result

T = TypeVar("T")

#: What a refusal means to a shell. Anything driving this from a script has to
#: be able to tell a method that is not there from one whose notation will not
#: parse, and both from the thing having worked.
EXIT_FOR: dict[Reason, int] = {
    Reason.NOT_FOUND: 3,
    Reason.ALREADY_EXISTS: 4,
    Reason.INVALID: 2,
}


def unwrap(result: Result[T]) -> T:
    """The value, or a message on stderr and the matching exit code."""
    if result.failure is not None:
        secho(str(result.failure), fg=RED, err=True)
        raise Exit(code=EXIT_FOR[result.failure.reason])
    return result.unwrap()


@dataclass(frozen=True, slots=True)
class Stores:
    """Every repository, all looking at the same transaction."""

    session: Session
    methods: MethodRepository
    performances: PerformanceRepository
    towers: TowerRepository
    ringers: RingerRepository
    competitions: CompetitionRepository
    compositions: CompositionRepository
    collections: CollectionRepository

    def commit(self) -> None:
        self.session.commit()


def show(renderable: object) -> None:
    """Print something to the terminal.

    Forty commands were each saying render.console().print(...), which meant
    forty places to change if the console ever needs an argument, and two of
    them had already started building the console differently.
    """
    from blueline.cli import render

    render.console().print(renderable)


def stores() -> Stores:
    """Open a session and build the repositories on it."""
    session = get_factory()()
    return Stores(
        session=session,
        methods=MethodRepository(session),
        performances=PerformanceRepository(session),
        towers=TowerRepository(session),
        ringers=RingerRepository(session),
        competitions=CompetitionRepository(session),
        compositions=CompositionRepository(session),
        collections=CollectionRepository(session),
    )


@contextmanager
def changing() -> Iterator[Stores]:
    """The repositories, committed if nothing raised.

    Nineteen commands were opening a session, doing one thing and calling
    commit, and a command that raised in between left the session open. Doing
    it here means a refusal rolls back rather than half applying, which
    matters for anything that touches two tables.
    """
    store = stores()
    try:
        yield store
    except BaseException:
        store.session.rollback()
        raise
    store.commit()
