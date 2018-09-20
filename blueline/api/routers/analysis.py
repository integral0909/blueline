"""Endpoints that work a method out without touching the library.

Analysing notation, drawing a line, listing falseness and so on. None of them
change anything, and keeping them apart from the endpoints that do means the
ones that write are all in one short file where they can be seen at a glance.
"""

from __future__ import annotations

from typing import Any, Dict, List

from blueline.api import stores
from blueline.api.convert import (
    comparison_out,
    dossier_out,
    false_course_head_out,
    handbell_pair_out,
    lead_head_group_out,
    line_out,
    method_out,
)
from blueline.api.routers.common import unwrap
from blueline.api.validate import body_of, path_whole, query_text, query_whole, text, whole
from blueline.api.wsgi import Request, Router
from blueline.service import analysing as service
from blueline.service import dossier
from blueline.service import library as library_service

router = Router(tag="methods")


@router.post("/analyse")
def analyse_method(request: Request) -> Dict[str, Any]:
    """Work a method out from its notation without storing anything."""
    body = body_of(request)
    report = unwrap(
        library_service.describe(
            text(body, "name", least=1, most=80),
            whole(body, "stage", least=3, most=16),
            text(body, "notation", least=1, most=2000),
        )
    )
    return method_out(report)


@router.get("/lead-head-groups")
def lead_head_groups(request: Request) -> List[Dict[str, Any]]:
    """The stored methods sorted into groups that take the same compositions."""
    stage = query_whole(request, "stage", least=3, most=16)
    views = unwrap(service.lead_head_groups(stores.methods(request), stage=stage))
    return [lead_head_group_out(view) for view in views]


@router.get("/methods/{title}/line/{bell}")
def get_line(request: Request, title: str, bell: str) -> Dict[str, Any]:
    wanted = path_whole(bell, "bell")
    return line_out(unwrap(service.line(stores.methods(request), title, wanted)))


@router.get("/methods/{title}/falseness")
def get_falseness(request: Request, title: str) -> List[Dict[str, Any]]:
    limit = query_whole(request, "limit", default=20, least=1, most=200)
    found = unwrap(service.falseness(stores.methods(request), title, limit=limit))
    return [false_course_head_out(entry) for entry in found]


@router.get("/methods/{title}/place-bells")
def get_place_bells(request: Request, title: str) -> List[int]:
    return unwrap(service.place_bells(stores.methods(request), title))


@router.get("/methods/{title}/handbells")
def get_handbells(request: Request, title: str) -> List[Dict[str, Any]]:
    """What each pair does, using the pairing nearly everybody uses."""
    views = unwrap(service.handbells(stores.methods(request), title))
    return [handbell_pair_out(view) for view in views]


@router.get("/methods/{title}/same-compositions")
def same_compositions(request: Request, title: str) -> List[str]:
    """Every other stored method a composition for this one would ring to."""
    return unwrap(service.takes_the_same_compositions(stores.methods(request), title))


@router.get("/methods/{title}/everything")
def method_dossier(request: Request, title: str) -> Dict[str, Any]:
    """Everything about one method, so a page needs one call rather than seven."""
    found = unwrap(
        dossier.compile_dossier(
            stores.methods(request),
            stores.compositions(request),
            stores.collections(request),
            title,
            bell=query_whole(request, "bell", default=2, least=1, most=16),
            most_falseness=query_whole(request, "falseness", default=12, least=1, most=200),
        )
    )
    return dossier_out(found)


@router.get("/methods/{title}/like")
def nearest_method(request: Request, title: str) -> Dict[str, Any]:
    """Whichever stored method this one is most like."""
    return comparison_out(unwrap(service.nearest_to(stores.methods(request), title)))


@router.get("/methods/{title}/vary/{kind}")
def vary_method(request: Request, title: str, kind: str) -> Dict[str, Any]:
    """The same method reversed, mirrored or doubled."""
    name = query_text(request, "name", most=80)
    return method_out(unwrap(service.vary(stores.methods(request), title, kind, name=name)))


@router.get("/methods/{title}/lead-end/{notation}")
def change_lead_end(request: Request, title: str, notation: str) -> Dict[str, Any]:
    """The same method with a different change at the lead end."""
    name = query_text(request, "name", most=80)
    return method_out(
        unwrap(service.change_lead_end(stores.methods(request), title, notation, name=name))
    )


@router.get("/methods/{title}/relation/{other}")
def method_relation(request: Request, title: str, other: str) -> Dict[str, str]:
    """How two stored methods are related, in words."""
    return {"relation": unwrap(service.relate(stores.methods(request), title, other))}


@router.get("/methods/{title}/against/{other}")
def compare_methods(request: Request, title: str, other: str) -> Dict[str, Any]:
    """How alike two stored methods are."""
    return comparison_out(unwrap(service.compare_methods(stores.methods(request), title, other)))
