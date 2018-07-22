"""A small http layer, written on what the standard library already has.

There is no web framework here on purpose. What this service does over http is
narrow: read a path, pull a few values out of the query string, hand back json.
A framework would bring routing, templating, sessions, forms and a dependency
system, and the only one of those it needs is the routing.

So: a router that turns "/methods/{title}/line/{bell}" into a regex, a request
that knows how to read a query string and a json body, and a response that
knows how to write one. Everything underneath is wsgiref, which has shipped
with Python since 2.5 and will still be there in ten years.

Handlers take a request and whatever the path captured, and give back either a
plain dict, which gets encoded as json, or a Response where they want to say
something about the status or the headers.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, Iterable, List, Optional, Pattern, Tuple
from urllib.parse import parse_qs

JSON = "application/json; charset=utf-8"
TEXT = "text/plain; charset=utf-8"

#: How a path variable is written, and what it becomes as a regex.
VARIABLE = re.compile(r"\{(\w+)\}")

STATUS_TEXT = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    503: "Service Unavailable",
}


class HttpError(Exception):
    """A refusal a handler wants to make, with the status to send back."""

    def __init__(self, status: int, reason: str, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.reason = reason
        self.detail = detail


class Response:
    """What goes back, for a handler that cares about more than the body."""

    def __init__(
        self,
        body: Any = None,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: str = JSON,
    ) -> None:
        self.body = body
        self.status = status
        self.headers = dict(headers or {})
        self.media_type = media_type

    def encoded(self) -> bytes:
        """The body as bytes.

        A handler that gives back a string has already written the body -
        exporting the library hands over json it built itself - so it goes out
        as it is. Anything else is a shape and gets encoded.
        """
        if self.body is None:
            return b""
        if isinstance(self.body, (bytes, bytearray)):
            return bytes(self.body)
        if isinstance(self.body, str):
            return self.body.encode("utf-8")
        return json.dumps(self.body, default=str).encode("utf-8")


class Request:
    """One request, as much of it as any handler here needs."""

    def __init__(self, environ: Dict[str, Any]) -> None:
        self.environ = environ
        self.method = environ.get("REQUEST_METHOD", "GET").upper()
        self.path = environ.get("PATH_INFO", "/") or "/"
        self._query = parse_qs(environ.get("QUERY_STRING", "") or "")
        self._body: Any = None
        self._read = False
        #: Anything the middleware wants to hang on the request.
        self.state: Dict[str, Any] = {}

    @property
    def headers(self) -> Dict[str, str]:
        found = {}
        for key, value in self.environ.items():
            if key.startswith("HTTP_"):
                found[key[5:].replace("_", "-").lower()] = value
        return found

    def header(self, name: str, default: str = "") -> str:
        return self.headers.get(name.lower(), default)

    def query(self, name: str, default: Optional[str] = None) -> Optional[str]:
        values = self._query.get(name)
        return values[0] if values else default

    def query_all(self, name: str) -> List[str]:
        return self._query.get(name, [])

    def json(self) -> Any:
        """The body, decoded.

        Read once and remembered. A wsgi input stream can only be consumed the
        one time, and a handler that looked at the body twice would find
        nothing the second time.
        """
        if self._read:
            return self._body
        self._read = True
        try:
            length = int(self.environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        raw = self.environ["wsgi.input"].read(length) if length else b""
        if not raw:
            self._body = None
            return None
        try:
            self._body = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise HttpError(400, "invalid", "the body is not json")
        return self._body


Handler = Callable[..., Any]


class Route:
    def __init__(self, method: str, path: str, handler: Handler) -> None:
        self.method = method
        self.path = path
        self.handler = handler
        self.pattern = self._compile(path)

    @staticmethod
    def _compile(path: str) -> Pattern[str]:
        # A path variable matches anything but a slash, so /methods/{title}
        # does not swallow /methods/a/b.
        escaped = re.escape(path).replace(r"\{", "{").replace(r"\}", "}")
        pattern = VARIABLE.sub(r"(?P<\1>[^/]+)", escaped)
        return re.compile(f"^{pattern}$")

    def match(self, path: str) -> Optional[Dict[str, str]]:
        found = self.pattern.match(path)
        return found.groupdict() if found else None


class Router:
    """Somewhere to hang a handful of routes.

    Order is kept, and matching walks it in order, so a literal path
    registered before a parameterised one wins. That is the same rule the
    routers were written to and there is a test that holds them to it.
    """

    def __init__(self, prefix: str = "", tag: str = "") -> None:
        self.prefix = prefix.rstrip("/")
        self.tag = tag
        self.routes: List[Route] = []

    def add(self, method: str, path: str, handler: Handler) -> None:
        self.routes.append(Route(method, self.prefix + path, handler))

    def _register(self, method: str, path: str) -> Callable[[Handler], Handler]:
        def keep(handler: Handler) -> Handler:
            self.add(method, path, handler)
            return handler

        return keep

    def get(self, path: str) -> Callable[[Handler], Handler]:
        return self._register("GET", path)

    def post(self, path: str) -> Callable[[Handler], Handler]:
        return self._register("POST", path)

    def delete(self, path: str) -> Callable[[Handler], Handler]:
        return self._register("DELETE", path)

    def paths(self) -> List[str]:
        return [route.path for route in self.routes]


def find(routers: Iterable[Router], method: str, path: str) -> Tuple[Optional[Route], bool]:
    """The route for a request, and whether the path matched something else.

    The second half is what tells a wrong method from a wrong path, which are
    different answers: 405 against 404.
    """
    seen = False
    for router in routers:
        for route in router.routes:
            if route.match(path) is None:
                continue
            seen = True
            if route.method == method:
                return route, True
    return None, seen
