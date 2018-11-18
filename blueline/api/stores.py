"""The repositories, built from the session a request is holding.

Twelve of these had grown across seven routers, all the same two lines under
whatever name suited the file. Two routers had each written their own methods
one, which meant two handlers in the same application could disagree about how
it is built.

They are here, once each, and named after what they hold. A handler says
stores.methods(request) and does not care where the session came from.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from blueline.db.repositories import (
    CollectionRepository,
    CompetitionRepository,
    CompositionRepository,
    MethodRepository,
    PerformanceRepository,
    RingerRepository,
    TowerRepository,
)


def session_of(request: Any) -> Session:
    """The session the application opened for this request."""
    return request.state["session"]


def methods(request: Any) -> MethodRepository:
    return MethodRepository(session_of(request))


def compositions(request: Any) -> CompositionRepository:
    return CompositionRepository(session_of(request))


def performances(request: Any) -> PerformanceRepository:
    return PerformanceRepository(session_of(request))


def towers(request: Any) -> TowerRepository:
    return TowerRepository(session_of(request))


def ringers(request: Any) -> RingerRepository:
    return RingerRepository(session_of(request))


def competitions(request: Any) -> CompetitionRepository:
    return CompetitionRepository(session_of(request))


def collections(request: Any) -> CollectionRepository:
    return CollectionRepository(session_of(request))
