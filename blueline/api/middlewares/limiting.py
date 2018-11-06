"""Refusing more requests than this is willing to answer.

Proving a touch is not a cheap request. A search for callings at major will
happily run for seconds, and a handful of those arriving together is enough to
make everything else wait. A limit does not make the service faster; it makes
the slowness somebody else's problem rather than everybody's.

Counted in a fixed window per caller. A sliding window is fairer and a token
bucket is smoother, and both need state this does not have anywhere sensible
to keep. One process, one dictionary, and the window resets on the minute.

That means the limit is per process rather than per service. Two workers behind
a load balancer allow twice as much between them, which is the honest thing to
say about it rather than something to hide: anything better needs somewhere
shared to count, and reaching for that before there is a second worker would be
building for a problem nobody has.
"""

from __future__ import annotations

import time
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Tuple

LIMIT_HEADER = "x-ratelimit-limit"
REMAINING_HEADER = "x-ratelimit-remaining"
RESET_HEADER = "x-ratelimit-reset"
RETRY_HEADER = "retry-after"

#: Requests one caller may make in a window. Generous: this is a brake on
#: something going wrong, not a business rule about fair use.
DEFAULT_LIMIT = 240
DEFAULT_WINDOW = 60.0

#: Never refused. A readiness probe that got a 429 would take the instance out
#: of the pool for being busy, which is the opposite of what anybody wants.
ALWAYS_ALLOWED = frozenset({"/health", "/ready"})


@dataclass(slots=True)
class Window:
    """How many requests a caller has made in the window it is in."""

    started: float
    count: int = 0

    def reset(self, now: float) -> None:
        self.started = now
        self.count = 0


@dataclass(slots=True)
class Counter:
    """Requests per caller, in fixed windows.

    Not thread safe, and deliberately not. Starlette runs one event loop, and
    a lock around a dictionary increment would cost more than the counting.
    """

    limit: int = DEFAULT_LIMIT
    window: float = DEFAULT_WINDOW
    callers: dict[str, Window] = field(default_factory=dict)

    def hit(self, caller: str, now: float) -> tuple[bool, int, float]:
        """Count a request. Says whether to allow it, what is left, and when
        the window turns over."""
        seen = self.callers.get(caller)
        if seen is None:
            seen = Window(started=now)
            self.callers[caller] = seen
        elif now - seen.started >= self.window:
            seen.reset(now)

        resets_in = self.window - (now - seen.started)
        if seen.count >= self.limit:
            return False, 0, resets_in
        seen.count += 1
        return True, self.limit - seen.count, resets_in

    def forget(self, before: float) -> int:
        """Drop callers whose window has long since turned over.

        Without this the dictionary grows one entry per address forever, which
        on a public service is a slow leak rather than a cache.
        """
        stale = [name for name, seen in self.callers.items() if seen.started < before]
        for name in stale:
            del self.callers[name]
        return len(stale)


def caller_of(environ: Dict[str, Any]) -> str:
    """Who is asking, as well as this can tell.

    The client address, which behind a proxy is the proxy. Trusting a
    forwarded header would let anybody set it and have their own bucket per
    request, so it is not read: a wrong answer that can be gamed is worse than
    a coarse one that cannot.
    """
    return environ.get("REMOTE_ADDR") or "unknown"


class RateLimiting:
    """Refuse a caller that is asking for more than its share."""

    def __init__(
        self,
        application: Callable[..., Any],
        limit: int = DEFAULT_LIMIT,
        window: float = DEFAULT_WINDOW,
    ) -> None:
        self.application = application
        self.counter = Counter(limit=limit, window=window)
        self._swept = 0.0

    def __call__(
        self, environ: Dict[str, Any], start_response: Callable[..., Any]
    ) -> Iterable[bytes]:
        if environ.get("PATH_INFO", "/") in ALWAYS_ALLOWED:
            return self.application(environ, start_response)

        now = time.monotonic()
        self._sweep(now)
        allowed, left, resets_in = self.counter.hit(caller_of(environ), now)
        if not allowed:
            return self._refused(start_response, resets_in)

        def capture(status: str, headers: List[Tuple[str, str]], *rest: Any) -> Any:
            headers = list(headers) + self._headers(left, resets_in)
            return start_response(status, headers, *rest)

        return self.application(environ, capture)

    def _sweep(self, now: float) -> None:
        """Clear out old callers, once a window rather than once a request."""
        if now - self._swept < self.counter.window:
            return
        self._swept = now
        self.counter.forget(now - self.counter.window * 2)

    def _refused(
        self, start_response: Callable[..., Any], resets_in: float
    ) -> Iterable[bytes]:
        retry = max(1, int(resets_in) + 1)
        body = json.dumps(
            {
                "reason": "too-many-requests",
                "detail": "more than {0} requests in {1} seconds".format(
                    self.counter.limit, int(self.counter.window)
                ),
            }
        ).encode("utf-8")
        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            (RETRY_HEADER, str(retry)),
        ]
        headers.extend(self._headers(0, resets_in))
        start_response("429 Too Many Requests", headers)
        return [body]

    def _headers(self, left: int, resets_in: float) -> List[Tuple[str, str]]:
        return [
            (LIMIT_HEADER, str(self.counter.limit)),
            (REMAINING_HEADER, str(left)),
            (RESET_HEADER, str(max(0, int(resets_in)))),
        ]
