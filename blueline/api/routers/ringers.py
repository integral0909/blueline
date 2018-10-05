"""Endpoints for the people who ring."""

from __future__ import annotations

from typing import Any, Dict, List

from blueline.api import stores
from blueline.api.convert import ringer_out
from blueline.api.paging import page_of, paging
from blueline.api.routers.common import unwrap
from blueline.api.validate import body_of, fail, listing, query_whole, text
from blueline.api.wsgi import Request, Response, Router
from blueline.service import ringers as service

router = Router(tag="ringers")


@router.post("/ringers")
def add_ringer(request: Request) -> Response:
    """Add somebody to the tower's list."""
    body = body_of(request)
    can_ring = [str(each) for each in listing(body, "can_ring", default=[], most=500)]
    learning = [str(each) for each in listing(body, "learning", default=[], most=500)]
    view = unwrap(
        service.add(
            stores.ringers(request),
            text(body, "name", least=1, most=80),
            can_ring,
            learning,
        )
    )
    return Response(ringer_out(view), status=201)


@router.get("/ringers")
def list_ringers(request: Request) -> Dict[str, Any]:
    """Everybody, in name order."""
    found = unwrap(service.everybody(stores.ringers(request)))
    return page_of([ringer_out(view) for view in found], paging(request))


# Above /ringers/{name}, or "learning" gets read as somebody's name.
@router.get("/ringers/learning")
def who_is_learning_what(request: Request) -> Dict[str, List[str]]:
    """What people are learning, and who else is learning it."""
    return unwrap(service.learning(stores.ringers(request)))


@router.get("/ringers/can-ring")
def what_the_band_can_ring(request: Request) -> Dict[str, Any]:
    """Which stored methods this band could actually get through."""
    stage = query_whole(request, "stage", least=3, most=16)
    if stage is None:
        raise fail("stage is needed")
    store = stores.ringers(request)
    titles = unwrap(service.what_can_be_rung(store, stores.methods(request), stage))
    return {"stage": stage, "ringers": store.count(), "titles": titles}


@router.post("/ringers/{name}/learnt")
def mark_learnt(request: Request, name: str) -> Dict[str, Any]:
    """Move a method from what somebody is learning to what they can ring."""
    title = text(body_of(request), "title", least=1, most=120)
    return ringer_out(unwrap(service.learnt(stores.ringers(request), name, title)))


@router.get("/ringers/{name}")
def get_ringer(request: Request, name: str) -> Dict[str, Any]:
    return ringer_out(unwrap(service.fetch(stores.ringers(request), name)))


@router.delete("/ringers/{name}")
def delete_ringer(request: Request, name: str) -> Response:
    unwrap(service.remove(stores.ringers(request), name))
    return Response(None, status=204)
