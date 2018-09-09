"""Endpoints for the rings of bells themselves."""

from __future__ import annotations

from typing import Any, Dict

from blueline.api import stores
from blueline.api.convert import annual_out, tower_out
from blueline.api.paging import page_of, paging
from blueline.api.routers.common import unwrap
from blueline.api.validate import body_of, path_whole, query_text, query_whole, text, whole
from blueline.api.wsgi import HttpError, Request, Response, Router
from blueline.service import annual
from blueline.service import towers as service
from blueline.service.annual import FIRST_YEAR

router = Router(tag="towers")


@router.post("/towers")
def add_tower(request: Request) -> Response:
    """Add a ring of bells."""
    body = body_of(request)
    view = unwrap(
        service.add(
            stores.towers(request),
            text(body, "place", least=1, most=160),
            whole(body, "bells", least=3, most=16),
            text(body, "tenor", least=1, most=16),
        )
    )
    return Response(tower_out(view), status=201)


@router.get("/towers")
def list_towers(request: Request) -> Dict[str, Any]:
    """Towers matching everything asked for, heaviest first."""
    found = unwrap(
        service.search(
            stores.towers(request),
            place=query_text(request, "place", most=160),
            min_bells=query_whole(request, "min_bells", least=3, most=16),
            max_bells=query_whole(request, "max_bells", least=3, most=16),
            min_tenor=query_text(request, "min_tenor", most=16),
        )
    )
    return page_of([tower_out(view) for view in found], paging(request))


# Above /towers/{place}, or a year gets read as part of the place.
@router.get("/towers/{place}/year/{year}")
def annual_report(request: Request, place: str, year: str) -> Dict[str, Any]:
    """Everything a tower puts in front of its AGM."""
    wanted = path_whole(year, "year")
    if not FIRST_YEAR <= wanted <= 2200:
        raise HttpError(422, "invalid", f"nobody was ringing changes in {wanted}")
    view = unwrap(
        annual.report(
            stores.performances(request),
            stores.ringers(request),
            stores.competitions(request),
            stores.collections(request),
            stores.methods(request),
            year=wanted,
            place=place,
            against=query_text(request, "against", default="the standard eight", most=120),
            top=query_whole(request, "top", default=5, least=1, most=50),
        )
    )
    return annual_out(view)


@router.get("/towers/{place}")
def get_tower(request: Request, place: str) -> Dict[str, Any]:
    return tower_out(unwrap(service.fetch(stores.towers(request), place)))


@router.delete("/towers/{place}")
def delete_tower(request: Request, place: str) -> Response:
    unwrap(service.remove(stores.towers(request), place))
    return Response(None, status=204)
