"""Endpoints about what to learn next."""

from __future__ import annotations

from typing import Any, Dict

from blueline.api import stores
from blueline.api.convert.learning import advice_out, difficulty_out
from blueline.api.paging import page_of, paging
from blueline.api.routers.common import unwrap
from blueline.api.validate import query_whole
from blueline.api.wsgi import Request, Router
from blueline.service import learning as service

router = Router(prefix="/learning", tag="learning")


@router.get("/order")
def ranked(request: Request) -> Dict[str, Any]:
    """The library in order of how hard it is, easiest first."""
    stage = query_whole(request, "stage", least=3, most=16)
    found = unwrap(service.rank(stores.methods(request), stage=stage))
    return page_of([difficulty_out(each) for each in found], paging(request))


@router.get("/band")
def for_the_band(request: Request) -> Dict[str, Any]:
    """What the whole band could learn together."""
    how_many = query_whole(request, "how_many", default=3, least=1, most=10)
    found = unwrap(
        service.advise_a_band(stores.methods(request), stores.ringers(request), how_many=how_many)
    )
    return page_of([difficulty_out(each) for each in found], paging(request))


@router.get("/methods/{title}")
def how_hard(request: Request, title: str) -> Dict[str, Any]:
    """What one method is going to ask of somebody."""
    return difficulty_out(unwrap(service.how_hard(stores.methods(request), title)))


@router.get("/ringers/{name}")
def advise(request: Request, name: str) -> Dict[str, Any]:
    """What a particular ringer should learn next."""
    how_many = query_whole(request, "how_many", default=3, least=1, most=10)
    view = unwrap(
        service.advise(
            stores.methods(request), stores.ringers(request), name, how_many=how_many
        )
    )
    return advice_out(view)
