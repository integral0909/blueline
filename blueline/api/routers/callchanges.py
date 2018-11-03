"""Endpoints for call change ringing.

Nothing is stored. A call change touch is called on the spot, and what a caller
wants back is where the calling went rather than a record of it.
"""

from __future__ import annotations

from typing import Any, Dict

from blueline.api.convert.callchanges import callchange_out
from blueline.api.routers.common import unwrap
from blueline.api.validate import body_of, one_of, text, whole
from blueline.api.wsgi import Request, Router
from blueline.service import callchanges as service

STYLES = ("up", "down")

router = Router(prefix="/callchanges", tag="call changes")


@router.post("/prove")
def prove_calling(request: Request) -> Dict[str, Any]:
    """Ring a calling through and say where it went."""
    body = body_of(request)
    calling = text(body, "calling", most=20000, strip=False)
    stage = whole(body, "stage", least=3, most=16)
    style = one_of(text(body, "style", default="down").lower(), STYLES, "style")
    start = text(body, "start", default="", most=16)
    report = unwrap(service.prove(calling, stage, style=style, start=start))
    return callchange_out(report, style)


@router.post("/route")
def route_to(request: Request) -> Dict[str, Any]:
    """The calls that take a band from where they are to somewhere else."""
    body = body_of(request)
    target = text(body, "target", least=1, most=32)
    stage = whole(body, "stage", least=3, most=16)
    start = text(body, "start", default="", most=16)
    return callchange_out(unwrap(service.how_to_get_to(target, stage, start=start)))
