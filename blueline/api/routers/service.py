"""Endpoints about the service itself rather than about ringing.

Liveness and readiness are separate on purpose. Liveness answers whether the
process is running and should never touch anything: a probe that fails because
the database is down gets the process restarted, which does not help. Readiness
answers whether traffic should be sent here, and that does have to look.
"""

from __future__ import annotations

from typing import Any, Dict

from blueline.api import stores
from blueline.api.convert import check_report_out
from blueline.api.routers.common import unwrap
from blueline.api.validate import query_flag
from blueline.api.wsgi import Request, Response, Router
from blueline.service import checking
from blueline.service import health as service

router = Router(tag="service")


@router.get("/health")
def health(request: Request) -> Dict[str, Any]:
    """Whether the process is up. Deliberately checks nothing."""
    return {"status": service.OK}


@router.get("/ready")
def ready(request: Request) -> Response:
    """Whether this instance can answer, which means asking the database."""
    report = service.readiness(stores.session_of(request))
    body = {
        "status": report.status,
        "ready": report.ready,
        "checks": [
            {
                "name": check.name,
                "status": check.status,
                "detail": check.detail,
                "took": round(check.took, 4),
            }
            for check in report.checks
        ],
    }
    return Response(body, status=200 if report.ready else 503)


@router.get("/check")
def check_library(request: Request) -> Dict[str, Any]:
    """Look over everything stored and say what is wrong.

    A get rather than a post, and deliberately: it changes nothing, and a
    caller should be able to hit it from a browser and a cron line alike.
    """
    thorough = query_flag(request, "thorough")
    return check_report_out(
        unwrap(
            checking.check(
                stores.methods(request),
                stores.compositions(request),
                stores.collections(request),
                stores.ringers(request),
                thorough=thorough,
            )
        )
    )
