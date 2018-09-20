"""Endpoints for planning a practice."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from blueline.api import stores
from blueline.api.convert import plan_out, term_out
from blueline.api.routers.common import unwrap
from blueline.api.validate import fail, query_flag, query_number, query_text, query_whole
from blueline.api.wsgi import Request, Router
from blueline.service import plans as service
from blueline.service import terms as service_terms

router = Router(tag="plans")


def _day(request: Request, name: str) -> date:
    """A date out of the query string, as YYYY-MM-DD."""
    raw = query_text(request, name, most=32)
    if not raw:
        raise fail(f"{name} is needed, as a date like 2018-09-04")
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise fail(f"{name}: {raw!r} is not a date like 2018-09-04")


@router.get("/plan")
def plan_practice(request: Request) -> Dict[str, Any]:
    """What a band could ring in the time, out of what is stored."""
    ringers = query_whole(request, "ringers", least=3, most=16)
    if ringers is None:
        raise fail("ringers is needed")
    minutes = query_whole(request, "minutes", least=1, most=600)
    if minutes is None:
        raise fail("minutes is needed")
    speed = query_number(request, "speed", default=30.0, least=0.1, most=60.0)
    band = stores.ringers(request)
    view = unwrap(
        service.plan(
            stores.methods(request),
            ringers=ringers,
            minutes=minutes,
            speed=speed,
            towers=stores.towers(request),
            place=query_text(request, "place", most=160),
            band=band if query_flag(request, "by_ability", default=True) else None,
        )
    )
    return plan_out(view)


@router.get("/plan/ringable")
def what_can_be_rung(request: Request) -> List[str]:
    """The methods a band of this size could ring."""
    ringers = query_whole(request, "ringers", least=3, most=16)
    if ringers is None:
        raise fail("ringers is needed")
    return unwrap(service.what_can_be_rung(stores.methods(request), ringers))


@router.get("/term")
def plan_the_term(request: Request) -> Dict[str, Any]:
    """A term's practice nights, with something against each."""
    weekday = query_whole(request, "weekday", default=1, least=0, most=6)
    view = unwrap(
        service_terms.plan_term(
            stores.methods(request),
            stores.ringers(request),
            stores.collections(request),
            _day(request, "first"),
            _day(request, "last"),
            weekday=weekday,
            working_from=query_text(request, "working_from", most=120),
        )
    )
    return term_out(view)
