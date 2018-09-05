"""Endpoints for what bands have actually rung."""

from __future__ import annotations

from typing import Any, Dict

from blueline.api import stores
from blueline.api.convert import performance_out, totals_out
from blueline.api.paging import page_of, paging
from blueline.api.routers.common import unwrap
from blueline.api.validate import (
    body_of,
    listing,
    number,
    path_whole,
    query_text,
    query_whole,
    text,
    whole,
)
from blueline.api.wsgi import TEXT, Request, Response, Router
from blueline.service import performances as service

router = Router(tag="performances")


@router.post("/performances")
def record_performance(request: Request) -> Response:
    """Write up something a band rang."""
    body = body_of(request)
    ringers = [str(each) for each in listing(body, "ringers", least=3, most=16)]
    view = unwrap(
        service.record(
            stores.performances(request),
            stores.methods(request),
            title=text(body, "title", least=1, most=120),
            stage=whole(body, "stage", least=3, most=16),
            length=whole(body, "length", least=1),
            rang_on=text(body, "rang_on", least=1, most=32),
            place=text(body, "place", least=1, most=160),
            ringers=ringers,
            conductor=text(body, "conductor", default=None, most=80) or None,
            composer=text(body, "composer", default=None, most=80) or None,
            peal_speed=number(body, "peal_speed", default=30.0, least=0.1, most=120),
            towers=stores.towers(request),
        )
    )
    return Response(performance_out(view), status=201)


@router.get("/performances")
def list_performances(request: Request) -> Dict[str, Any]:
    """Performances matching everything asked for, most recent first."""
    found = unwrap(
        service.search(
            stores.performances(request),
            place=query_text(request, "place", most=160),
            title=query_text(request, "title", most=120),
            stage=query_whole(request, "stage", least=3, most=16),
            min_length=query_whole(request, "min_length", least=1),
            ringer=query_text(request, "ringer", most=80),
        )
    )
    return page_of([performance_out(view) for view in found], paging(request))


@router.post("/performances/report")
def record_from_report(request: Request) -> Response:
    """File a performance somebody pasted in as a report."""
    body = body_of(request)
    view = unwrap(
        service.from_report(
            stores.performances(request),
            stores.methods(request),
            text(body, "report", least=1, most=20000, strip=False),
            whole(body, "stage", least=3, most=16),
            towers=stores.towers(request),
        )
    )
    return Response(performance_out(view), status=201)


# Above /performances/{performance_id}, or "totals" gets read as an id.
@router.get("/performances/totals")
def performance_totals(request: Request) -> Dict[str, Any]:
    """What the performances add up to."""
    totals = unwrap(
        service.statistics(
            stores.performances(request),
            place=query_text(request, "place", most=160),
            ringer=query_text(request, "ringer", most=80),
        )
    )
    return totals_out(totals, top=query_whole(request, "top", default=10, least=1, most=100))


@router.get("/performances/{performance_id}/board")
def performance_board(request: Request, performance_id: str) -> Response:
    """One performance laid out as it would be painted on a wall."""
    width = query_whole(request, "width", default=44, least=20, most=120)
    written = unwrap(
        service.board(
            stores.performances(request),
            path_whole(performance_id, "performance"),
            width=width,
        )
    )
    return Response(written, media_type=TEXT)


@router.get("/performances/{performance_id}/report")
def performance_report(request: Request, performance_id: str) -> Response:
    """One performance written up ready to be pasted in.

    Plain text like the board, and for the same reason: this is something
    somebody copies, and handing it over as a json string with the newlines
    escaped in it would make the copying worse.
    """
    written = unwrap(
        service.report(stores.performances(request), path_whole(performance_id, "performance"))
    )
    return Response(written, media_type=TEXT)


@router.get("/performances/{performance_id}")
def get_performance(request: Request, performance_id: str) -> Dict[str, Any]:
    wanted = path_whole(performance_id, "performance")
    return performance_out(unwrap(service.fetch(stores.performances(request), wanted)))
