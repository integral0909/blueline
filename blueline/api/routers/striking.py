"""Endpoints for judging striking.

Nothing here is stored. A competition is judged on the day and the marking
goes on a sheet of paper, so these take what somebody recorded and hand back
what it came to.
"""

from __future__ import annotations

from typing import Any, Dict, List

from blueline.api.convert.striking import order_out, striking_out
from blueline.api.routers.common import unwrap
from blueline.api.validate import body_of, fail, listing, number, text, whole
from blueline.api.wsgi import Request, Router
from blueline.service import striking as service

#: Nobody hands in one blow, and a peal is around fifteen thousand. Past that
#: the request is a mistake and refusing is kinder than judging it.
MOST_BLOWS = 20000

router = Router(prefix="/striking", tag="striking")


def _times(raw: List[Any], name: str) -> List[float]:
    """Blow times, which have to be numbers and have to be in order."""
    if len(raw) < 2:
        raise fail(f"{name} needs at least two blows")
    if len(raw) > MOST_BLOWS:
        raise fail(f"{name} has more blows than anybody rings")
    times = []
    for each in raw:
        try:
            times.append(float(each))
        except (TypeError, ValueError):
            raise fail(f"{name}: {each!r} is not a time")
    if any(later <= earlier for earlier, later in zip(times, times[1:])):
        raise fail(f"{name}: blows have to be struck in order")
    return times


@router.post("/mark")
def mark_attempt(request: Request) -> Dict[str, Any]:
    """Judge one band's attempt."""
    body = body_of(request)
    band = text(body, "band", least=1, most=120)
    stage = whole(body, "stage", least=1, most=16)
    threshold = number(body, "threshold", default=0.10, least=0.0001, most=0.9999)
    times = _times(listing(body, "times", most=MOST_BLOWS), "times")
    return striking_out(unwrap(service.mark(band, times, stage, threshold=threshold)))


@router.post("/order")
def order_competition(request: Request) -> Dict[str, Any]:
    """Put a competition's bands in order of merit."""
    body = body_of(request)
    stage = whole(body, "stage", least=1, most=16)
    threshold = number(body, "threshold", default=0.10, least=0.0001, most=0.9999)
    attempts = body.get("attempts")
    if not isinstance(attempts, dict) or not attempts:
        raise fail("attempts has to name at least one band")
    marked = {band: _times(list(raw), band) for band, raw in attempts.items()}
    reports = unwrap(service.order_of_merit(marked, stage, threshold=threshold))
    return order_out(stage, reports)
