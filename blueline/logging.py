"""Logging, set up once and structured.

Print statements and a bare logger both fall down the moment anybody has to
find out what happened during a request that went wrong in production. What is
wanted is a line per event with the fields attached rather than baked into a
sentence, so a search can ask for everything about one method rather than
grepping for a title and hoping.

Two shapes. Development gets colours and one line per event because a person is
reading it. Anything else gets json, because a machine is.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, List

import structlog

DEV = "dev"
JSON = "json"


def _shared_processors() -> List[Any]:
    """The processors both shapes want, in the order they have to run."""
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]


def configure(shape: str = JSON, level: int = logging.INFO) -> None:
    """Set logging up. Safe to call twice, which tests do."""
    renderer: Any
    if shape == DEV:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())
    else:
        renderer = structlog.processors.JSONRenderer(sort_keys=True)

    structlog.configure(
        processors=[*_shared_processors(), structlog.processors.format_exc_info, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=False,
    )


def get_logger(name: str) -> Any:
    """A logger that knows where it came from.

    The name is bound as a field rather than being read off the logger.
    structlog's add_logger_name wants a standard library logger underneath and
    we are printing straight to stderr, which has no name to read.
    """
    return structlog.get_logger().bind(logger=name)


def bind(**fields: Any) -> None:
    """Attach fields to everything logged from here on in this context.

    Used for a request id, so every line a request produces can be found
    without threading the id through every call.
    """
    structlog.contextvars.bind_contextvars(**fields)


def unbind(*names: str) -> None:
    structlog.contextvars.unbind_contextvars(*names)


def clear() -> None:
    structlog.contextvars.clear_contextvars()
