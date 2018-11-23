"""Endpoints for named sets of methods."""

from __future__ import annotations

from typing import Any, Dict

from blueline.api import stores
from blueline.api.convert.collections import collection_out, coverage_out
from blueline.api.paging import page_of, paging
from blueline.api.routers.common import unwrap
from blueline.api.validate import body_of, listing, query_flag, query_text, text
from blueline.api.wsgi import Request, Response, Router
from blueline.service import collections as service

#: The core refuses anything bigger, but refusing it here means a caller who
#: pasted a whole library in gets told so rather than having it read first.
MOST_TITLES = 200

router = Router(prefix="/collections", tag="collections")


@router.post("")
def keep_collection(request: Request) -> Response:
    """Write a set of methods down."""
    body = body_of(request)
    titles = [str(each) for each in listing(body, "titles", default=[], most=MOST_TITLES)]
    view = unwrap(
        service.keep(
            stores.collections(request),
            stores.methods(request),
            text(body, "name", least=1, most=120),
            titles,
            note=text(body, "note", default="", most=500),
        )
    )
    return Response(collection_out(view), status=201)


@router.get("")
def list_collections(request: Request) -> Dict[str, Any]:
    """Every set, stored or named."""
    found = unwrap(
        service.listing(
            stores.collections(request),
            stores.methods(request),
            include_known=query_flag(request, "include_known", default=True),
        )
    )
    return page_of([collection_out(view) for view in found], paging(request))


@router.get("/{name}/coverage")
def collection_coverage(request: Request, name: str) -> Dict[str, Any]:
    """How much of a set a ringer, or the whole band, rings."""
    who = query_text(request, "who", most=80)
    return coverage_out(
        unwrap(
            service.coverage(
                stores.collections(request), stores.ringers(request), name, who=who
            )
        )
    )


@router.get("/{name}")
def get_collection(request: Request, name: str) -> Dict[str, Any]:
    return collection_out(
        unwrap(service.fetch(stores.collections(request), stores.methods(request), name))
    )


@router.post("/{name}/methods")
def add_to_collection(request: Request, name: str) -> Dict[str, Any]:
    """Put a method into a stored set."""
    title = text(body_of(request), "title", least=1, most=120)
    return collection_out(
        unwrap(service.add_to(stores.collections(request), stores.methods(request), name, title))
    )


@router.delete("/{name}/methods/{title}")
def take_out_of_collection(request: Request, name: str, title: str) -> Dict[str, Any]:
    """Take a method out of a stored set."""
    return collection_out(
        unwrap(service.take_out(stores.collections(request), stores.methods(request), name, title))
    )


@router.delete("/{name}")
def forget_collection(request: Request, name: str) -> Response:
    unwrap(service.forget(stores.collections(request), name))
    return Response(None, status=204)
