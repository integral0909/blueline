"""The application itself, as a wsgi callable.

Thin on purpose. Building the app and deciding what it talks to are separate,
so a test can build one against an in memory database without the module
import having already opened a file somewhere.

What it does for every request: open a session, find a route, call the handler,
turn what comes back into json, and close the session. Errors of every kind end
up in one envelope, because a client writing error handling should not have to
work out where in the stack a refusal came from.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional

from blueline.api.deps import configure, get_factory, get_settings
from blueline.api.middlewares import RateLimiting, RequestLogging
from blueline.api.routers import ROUTERS
from blueline.api.wsgi import STATUS_TEXT, HttpError, Request, Response, Router, find
from blueline.config import Settings
from blueline.errors import BluelineError, LibraryError
from blueline.logging import get_logger

TITLE = "blueline"
DESCRIPTION = "Change ringing method analysis and composition proving"
VERSION = "0.1.0"
LOGGER_NAME = "blueline.api"

#: What a refusal means when the library raised it rather than a service.
#: LibraryError means something was not there; everything else means what was
#: asked for does not make sense.
STATUS_FOR_ERROR = {LibraryError: 404}
DEFAULT_STATUS = 422


def status_for(error: BluelineError) -> int:
    for kind, code in STATUS_FOR_ERROR.items():
        if isinstance(error, kind):
            return code
    return DEFAULT_STATUS


def envelope(request: Request, status: int, reason: str, detail: str) -> Response:
    """One shape for every refusal."""
    body: Dict[str, Any] = {"reason": reason, "detail": detail}
    request_id = request.state.get("request_id", "")
    if request_id:
        body["request_id"] = request_id
    return Response(body, status=status)


class Application:
    """The wsgi callable, and the routers it serves."""

    def __init__(self, routers: Iterable[Router]) -> None:
        self.routers: List[Router] = list(routers)

    def paths(self) -> List[str]:
        return [path for router in self.routers for path in router.paths()]

    def handle(self, request: Request) -> Response:
        route, path_seen = find(self.routers, request.method, request.path)
        if route is None:
            if path_seen:
                return envelope(
                    request, 405, "refused", f"{request.method} is not allowed here"
                )
            return envelope(request, 404, "not-found", f"nothing is served at {request.path}")

        params = route.match(request.path) or {}
        factory = get_factory()
        session = factory()
        request.state["session"] = session
        try:
            found = route.handler(request, **params)
            session.commit()
        except HttpError as error:
            session.rollback()
            return envelope(request, error.status, error.reason, error.detail)
        except BluelineError as error:
            session.rollback()
            return envelope(request, status_for(error), "refused", str(error))
        except Exception:
            session.rollback()
            # A bug. The traceback goes to the log, where it is some use; a
            # caller cannot act on the inside of a stack trace and a public
            # service should not hand one out.
            get_logger(LOGGER_NAME).exception("unhandled", path=request.path)
            return envelope(request, 500, "error", "something went wrong")
        finally:
            session.close()

        if isinstance(found, Response):
            return found
        return Response(found)

    def __call__(
        self, environ: Dict[str, Any], start_response: Callable[..., Any]
    ) -> Iterable[bytes]:
        request = Request(environ)
        response = self.handle(request)
        body = response.encoded()
        headers = [("Content-Type", response.media_type), ("Content-Length", str(len(body)))]
        headers.extend(response.headers.items())
        line = f"{response.status} {STATUS_TEXT.get(response.status, 'Unknown')}"
        start_response(line, headers)
        return [body] if body else []


def create_app(settings: Optional[Settings] = None) -> Any:
    """Build the application, optionally pointed at a particular database."""
    configured = configure(settings) if settings is not None else get_settings()
    app: Any = Application(ROUTERS)
    # Limiting goes on first and logging second, so logging ends up outermost.
    # A request refused for going over the limit is still worth a line, and
    # that line is the only thing that says the limit is doing anything.
    app = RateLimiting(
        app, limit=configured.request_limit, window=configured.request_window
    )
    app = RequestLogging(app)
    return app


app = create_app()
