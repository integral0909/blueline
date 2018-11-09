"""Endpoints for the compositions somebody has written down.

Everything is proved on the way in and again on the way out, so a client
never sees a length or a truth that was only ever a claim.
"""

from __future__ import annotations

from typing import Any, Dict

from blueline.api import stores
from blueline.api.convert.compositions import composition_out
from blueline.api.paging import page_of, paging
from blueline.api.routers.common import unwrap
from blueline.api.validate import body_of, path_whole, query_text, query_whole, text
from blueline.api.wsgi import Request, Response, Router
from blueline.service import compositions as service

router = Router(prefix="/compositions", tag="compositions")


@router.post("")
def store_composition(request: Request) -> Response:
    """Prove a touch and keep it."""
    body = body_of(request)
    view = unwrap(
        service.store(
            stores.compositions(request),
            stores.methods(request),
            title=text(body, "title", least=1, most=120),
            method_title=text(body, "method", least=1, most=120),
            calling=text(body, "calling", least=1, most=2000),
            composer=text(body, "composer", default="", most=80),
        )
    )
    return Response(composition_out(view), status=201)


@router.get("")
def list_compositions(request: Request) -> Dict[str, Any]:
    """Everything written for one method, or the longest in the library."""
    method = query_text(request, "method", most=120)
    store = stores.compositions(request)
    methods = stores.methods(request)
    if method is not None:
        found = unwrap(service.for_method(store, methods, method))
    else:
        limit = query_whole(request, "limit", default=10, least=1, most=200)
        found = unwrap(service.longest(store, methods, limit=limit))
    return page_of([composition_out(view) for view in found], paging(request))


@router.get("/{composition_id}")
def get_composition(request: Request, composition_id: str) -> Dict[str, Any]:
    wanted = path_whole(composition_id, "composition")
    view = unwrap(service.fetch(stores.compositions(request), stores.methods(request), wanted))
    return composition_out(view)


@router.delete("/{composition_id}")
def delete_composition(request: Request, composition_id: str) -> Response:
    unwrap(service.remove(stores.compositions(request), path_whole(composition_id, "composition")))
    return Response(None, status=204)
