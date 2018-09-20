"""Endpoints that change what is in the library.

Storing a method, taking one out, listing what is there and moving collections
in and out. Everything here writes or reads the library itself; anything that
only works a method out lives in analysis.
"""

from __future__ import annotations

from typing import Any, Dict

from blueline.api import stores
from blueline.api.convert import import_out, method_out
from blueline.api.paging import page_of, paging
from blueline.api.routers.common import unwrap
from blueline.api.validate import body_of, one_of, query_text, query_whole, text, whole
from blueline.api.wsgi import JSON, TEXT, Request, Response, Router
from blueline.service import library as service

router = Router(tag="methods")


@router.get("/methods")
def list_methods(request: Request) -> Dict[str, Any]:
    found = unwrap(
        service.search(
            stores.methods(request),
            name=query_text(request, "name", most=80),
            stage=query_whole(request, "stage", least=3, most=16),
            classification=query_text(request, "classification", most=40),
        )
    )
    return page_of([method_out(report) for report in found], paging(request))


@router.post("/methods")
def store_method(request: Request) -> Response:
    body = body_of(request)
    name = text(body, "name", least=1, most=80)
    stage = whole(body, "stage", least=3, most=16)
    notation = text(body, "notation", least=1, most=2000)
    unwrap(service.store(stores.methods(request), name, stage, notation))
    return Response(method_out(unwrap(service.describe(name, stage, notation))), status=201)


# These two go above /methods/{title}. Routes match in the order they were
# registered, so with the parameterised one first "export" gets read as the
# title of a method nobody has and the endpoint answers 404.


@router.post("/methods/import")
def import_methods(request: Request) -> Dict[str, Any]:
    """Read a collection of methods into the library."""
    document = text(body_of(request), "body", least=1, most=2_000_000, strip=False)
    return import_out(unwrap(service.import_methods(stores.methods(request), document)))


@router.get("/methods/export")
def export_methods(request: Request) -> Response:
    """The library as a file, in whichever shape was asked for."""
    asked = query_text(request, "shape", default="json") or "json"
    shape = one_of(asked, ("json", "lines"), "shape")
    stage = query_whole(request, "stage", least=3, most=16)
    written = unwrap(service.export_methods(stores.methods(request), shape=shape, stage=stage))
    return Response(written, media_type=JSON if shape == "json" else TEXT)


@router.get("/methods/{title}")
def get_method(request: Request, title: str) -> Dict[str, Any]:
    return method_out(unwrap(service.fetch(stores.methods(request), title)))


@router.delete("/methods/{title}")
def delete_method(request: Request, title: str) -> Response:
    """Nothing comes back."""
    unwrap(service.remove(stores.methods(request), title))
    return Response(None, status=204)
