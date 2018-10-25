"""Endpoints for striking competitions.

Two ways to write one up, because there are two ways it happens: post the
sheet the judge announced, or post what was recorded and let the marking
decide the order.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict

from blueline.api import stores
from blueline.api.convert.competitions import competition_out, progress_out
from blueline.api.paging import page_of, paging
from blueline.api.routers.common import unwrap
from blueline.api.validate import (
    body_of,
    fail,
    listing,
    number,
    path_whole,
    query_text,
    query_whole,
    text,
    whole,
)
from blueline.api.wsgi import Request, Response, Router
from blueline.core.competitions import Entry
from blueline.service import competitions as service

router = Router(prefix="/competitions", tag="competitions")


def _held_on(body: Dict[str, Any]) -> date:
    raw = text(body, "held_on", least=1, most=32)
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise fail(f"held_on: {raw!r} is not a date like 2018-09-04")


def _entries(body: Dict[str, Any]) -> tuple:
    raw = listing(body, "entries", least=1, most=200)
    entries = []
    seen = set()
    for each in raw:
        if not isinstance(each, dict):
            raise fail("every entry has to be an object")
        band = text(each, "band", least=1, most=120)
        if band.lower() in seen:
            raise fail("a band cannot enter twice")
        seen.add(band.lower())
        entries.append(
            Entry(
                band=band,
                position=whole(each, "position", least=1, most=200),
                faults=whole(each, "faults", least=0, most=100000),
                percentage=number(each, "percentage", default=0.0, least=0, most=100),
                drift=text(each, "drift", default="", most=16),
                note=text(each, "note", default="", most=500),
            )
        )
    return tuple(entries)


@router.post("/judged")
def judge_competition(request: Request) -> Response:
    """Mark what was recorded, then write up the sheet it comes to."""
    body = body_of(request)
    attempts = body.get("attempts")
    if not isinstance(attempts, dict) or not attempts:
        raise fail("attempts has to name at least one band")
    for band, times in attempts.items():
        if not isinstance(times, list) or len(times) < 2:
            raise fail(f"{band} needs at least two blows")
    view = unwrap(
        service.judge_and_record(
            stores.competitions(request),
            name=text(body, "name", least=1, most=120),
            held_on=_held_on(body),
            stage=whole(body, "stage", least=1, most=16),
            attempts={band: [float(t) for t in times] for band, times in attempts.items()},
            place=text(body, "place", default="", most=160),
            judge=text(body, "judge", default="", most=120),
        )
    )
    return Response(competition_out(view), status=201)


@router.post("")
def record_competition(request: Request) -> Response:
    """Write up a sheet the judge announced."""
    body = body_of(request)
    view = unwrap(
        service.record(
            stores.competitions(request),
            name=text(body, "name", least=1, most=120),
            held_on=_held_on(body),
            stage=whole(body, "stage", least=1, most=16),
            entries=_entries(body),
            place=text(body, "place", default="", most=160),
            judge=text(body, "judge", default="", most=120),
        )
    )
    return Response(competition_out(view), status=201)


@router.get("")
def list_competitions(request: Request) -> Dict[str, Any]:
    """Sheets matching everything asked for, most recent first."""
    found = unwrap(
        service.listing(
            stores.competitions(request),
            name=query_text(request, "name", most=120),
            place=query_text(request, "place", most=160),
            band=query_text(request, "band", most=120),
            stage=query_whole(request, "stage", least=1, most=16),
        )
    )
    return page_of([competition_out(view) for view in found], paging(request))


# Above /{competition_id}, or a band name gets read as an id.
@router.get("/bands/{band}")
def band_progress(request: Request, band: str) -> Dict[str, Any]:
    """Where a band has come each year it entered."""
    return progress_out(unwrap(service.band_progress(stores.competitions(request), band)))


@router.get("/{competition_id}")
def get_competition(request: Request, competition_id: str) -> Dict[str, Any]:
    wanted = path_whole(competition_id, "competition")
    return competition_out(unwrap(service.fetch(stores.competitions(request), wanted)))


@router.delete("/{competition_id}")
def delete_competition(request: Request, competition_id: str) -> Response:
    unwrap(service.remove(stores.competitions(request), path_whole(competition_id, "competition")))
    return Response(None, status=204)
