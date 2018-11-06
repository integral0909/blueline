"""Giving every request an id, and timing it.

The id is bound into the logging context so all the lines one request produces
can be found together, and handed back in a header so somebody reporting a
problem can quote it. The timing means a search that takes four seconds shows
up as a number rather than as a complaint.

The id comes off the request where the caller supplied one. A proxy or a
client already tracking a request across services should not have its id
thrown away and replaced.

Written as wsgi middleware, which is a callable wrapping a callable. The only
awkward part is that the status is not known until the application calls
start_response, so that gets wrapped too.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable, Dict, Iterable, List, Tuple

from blueline.logging import bind, clear, get_logger

REQUEST_ID_HEADER = "x-request-id"
DURATION_HEADER = "x-response-time-ms"
LOGGER_NAME = "blueline.api"


def request_id_of(environ: Dict[str, Any]) -> str:
    """The caller's id where there is one, otherwise a fresh one."""
    supplied = environ.get("HTTP_X_REQUEST_ID", "").strip()
    return supplied or uuid.uuid4().hex


class RequestLogging:
    """Give every request an id, time it, and say what happened."""

    def __init__(self, application: Callable[..., Any]) -> None:
        self.application = application

    def __call__(
        self, environ: Dict[str, Any], start_response: Callable[..., Any]
    ) -> Iterable[bytes]:
        # Fetched per request rather than at import. A logger bound before
        # logging is configured keeps the configuration it was born with, and
        # the application is built before anybody calls configure.
        log = get_logger(LOGGER_NAME)
        request_id = request_id_of(environ)
        # On the environ as well as in the log context, so a handler can quote
        # the same id the log line carries.
        environ["blueline.request_id"] = request_id
        path = environ.get("PATH_INFO", "/")
        method = environ.get("REQUEST_METHOD", "GET")
        bind(request_id=request_id, path=path, method=method)
        started = time.perf_counter()
        seen: Dict[str, Any] = {}

        def capture(status: str, headers: List[Tuple[str, str]], *rest: Any) -> Any:
            seen["status"] = status
            elapsed = _since(started)
            headers = list(headers)
            headers.append((REQUEST_ID_HEADER, request_id))
            headers.append((DURATION_HEADER, f"{elapsed:.1f}"))
            return start_response(status, headers, *rest)

        try:
            body = self.application(environ, capture)
        except Exception:
            log.exception("request failed", elapsed_ms=_since(started))
            clear()
            raise

        code = int(str(seen.get("status", "500")).split(" ")[0])
        log.info("request", status=code, elapsed_ms=_since(started))
        clear()
        return body


def _since(started: float) -> float:
    return (time.perf_counter() - started) * 1000
