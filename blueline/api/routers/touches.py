"""Endpoints for proving touches and looking for them."""

from __future__ import annotations

from typing import Any, Dict, List

from blueline.api import stores
from blueline.api.convert import (
    music_search_out,
    position_out,
    printed_out,
    search_out,
    splice_out,
    target_out,
    touch_out,
)
from blueline.api.routers.common import unwrap
from blueline.api.validate import (
    body_of,
    fail,
    listing,
    query_text,
    query_whole,
    text,
    whole,
)
from blueline.api.wsgi import Request, Router
from blueline.service import calls as call_service
from blueline.service import proving as touch_service
from blueline.service import searching as search_service
from blueline.service import spliced as splice_service

router = Router(tag="touches")


@router.get("/methods/{title}/course")
def get_course(request: Request, title: str) -> Dict[str, Any]:
    """The plain course, reported the way a touch is."""
    return touch_out(unwrap(touch_service.course_of(stores.methods(request), title)))


@router.post("/methods/{title}/prove")
def prove_touch(request: Request, title: str) -> Dict[str, Any]:
    """Ring a touch through and say whether it comes round and is true."""
    body = body_of(request)
    calling = text(body, "calling", least=1, most=2000)
    times = whole(body, "times", default=1, least=1, most=500)
    return touch_out(
        unwrap(touch_service.prove(stores.methods(request), title, calling, times=times))
    )


@router.get("/methods/{title}/search")
def search_callings(request: Request, title: str) -> Dict[str, Any]:
    """Callings of a stored method that come round and are true."""
    report = unwrap(
        search_service.search(
            stores.methods(request),
            title,
            min_length=query_whole(request, "min_length", default=1, least=1, most=100_000),
            max_length=query_whole(request, "max_length", default=5040, least=1, most=100_000),
            max_found=query_whole(request, "max_found", default=20, least=1, most=200),
            allowed=query_text(request, "allowed", most=8),
        )
    )
    return search_out(report)


@router.get("/methods/{title}/for-length")
def callings_for_length(request: Request, title: str) -> Dict[str, Any]:
    """Callings that come to a particular length."""
    length = query_whole(request, "length", least=1, most=100_000)
    if length is None:
        raise fail("length is needed")
    report = unwrap(
        search_service.for_length(
            stores.methods(request),
            title,
            length,
            tolerance=query_whole(request, "tolerance", default=0, least=0, most=10_000),
            max_found=query_whole(request, "max_found", default=10, least=1, most=100),
            allowed=query_text(request, "allowed", most=8),
        )
    )
    return target_out(report)


@router.get("/methods/{title}/musical")
def musical_touches(request: Request, title: str) -> Dict[str, Any]:
    """The most musical callings a search turns up."""
    report = unwrap(
        search_service.most_musical(
            stores.methods(request),
            title,
            min_length=query_whole(request, "min_length", default=1, least=1),
            max_length=query_whole(request, "max_length", default=5040, least=1),
            max_found=query_whole(request, "max_found", default=200, least=1, most=2000),
            how_many=query_whole(request, "how_many", default=10, least=1, most=100),
            allowed=query_text(request, "allowed", most=8),
            min_run=query_whole(request, "min_run", default=4, least=3, most=8),
        )
    )
    return music_search_out(report)


@router.get("/methods/{title}/positions")
def calling_positions(request: Request, title: str) -> List[Dict[str, Any]]:
    """The named places in the course where a call can be made."""
    views = unwrap(call_service.positions(stores.methods(request), title))
    return [position_out(view) for view in views]


@router.post("/methods/{title}/call")
def prove_called(request: Request, title: str) -> Dict[str, Any]:
    """Prove a touch written the way a conductor calls it."""
    called = [str(each) for each in listing(body_of(request), "called", most=500)]
    return touch_out(unwrap(call_service.prove_positions(stores.methods(request), title, called)))


@router.post("/methods/{title}/printed")
def prove_printed(request: Request, title: str) -> Dict[str, Any]:
    """Prove a composition written the way it is published."""
    printed = text(body_of(request), "printed", least=1, most=2000)
    return printed_out(unwrap(call_service.prove_printed(stores.methods(request), title, printed)))


@router.post("/splice")
def prove_splice(request: Request) -> Dict[str, Any]:
    """Ring a spliced touch through and say whether it works."""
    body = body_of(request)
    titles = [str(each) for each in listing(body, "titles", least=1, most=50)]
    report = unwrap(
        splice_service.splice(
            stores.methods(request),
            titles,
            text(body, "order", least=1, most=2000),
            calling=text(body, "calling", default="", most=2000),
        )
    )
    return splice_out(report)
