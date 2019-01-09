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
import threading
from typing import Any, List, TextIO, cast

import structlog

DEV = "dev"
JSON = "json"


class _Context(threading.local):
    """Whatever has been bound for the request this thread is serving."""

    def __init__(self) -> None:
        self.fields: dict = {}


_CONTEXT = _Context()


class _CurrentStderr:
    """A stand in for sys.stderr that is looked up at the moment of writing.

    Handing structlog sys.stderr directly captures whatever stream was there
    when logging was configured. Anything that swaps the stream afterwards, and
    pytest does it around every test, leaves the logger holding a file that
    gets closed underneath it.
    """

    def write(self, text: str) -> int:
        return sys.stderr.write(text)

    def flush(self) -> None:
        sys.stderr.flush()

    @property
    def closed(self) -> bool:
        return bool(getattr(sys.stderr, "closed", False))


STDERR = _CurrentStderr()


def _shared_processors() -> List[Any]:
    """The processors both shapes want, in the order they have to run."""
    return [
        merge_context,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]


def _at_least(level: int) -> Any:
    """Drop anything logged below the level that was asked for.

    structlog's own filter wants a standard library logger underneath it to
    ask isEnabledFor, and we print straight to stderr. The method name is on
    every event anyway, so the comparison is a lookup.
    """
    names = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "warn": logging.WARNING,
        "error": logging.ERROR,
        "exception": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    def keep(_logger: Any, method_name: str, event: Any) -> Any:
        if names.get(method_name, logging.INFO) < level:
            raise structlog.DropEvent
        return event

    return keep


def _is_a_terminal() -> bool:
    try:
        return bool(sys.stderr.isatty())
    except (AttributeError, ValueError):
        return False


def configure(shape: str = JSON, level: int = logging.INFO) -> None:
    """Set logging up. Safe to call twice, which tests do."""
    renderer: Any
    if shape == DEV:
        renderer = structlog.dev.ConsoleRenderer(colors=_is_a_terminal())
    else:
        renderer = structlog.processors.JSONRenderer(sort_keys=True)

    structlog.configure(
        processors=[
            _at_least(level),
            *_shared_processors(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.BoundLogger,
        # PrintLoggerFactory is annotated as wanting a TextIO. It only ever
        # calls write and flush, which is all the stand in offers.
        logger_factory=structlog.PrintLoggerFactory(file=cast(TextIO, STDERR)),
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
    """Attach fields to everything logged from here on in this thread.

    Used for a request id, so every line a request produces can be found
    without threading the id through every call.
    """
    _CONTEXT.fields.update(fields)


def unbind(*names: str) -> None:
    for name in names:
        _CONTEXT.fields.pop(name, None)


def clear() -> None:
    _CONTEXT.fields.clear()


def merge_context(_logger: Any, _name: str, event: Any) -> Any:
    """Put the bound fields on the event as it goes past.

    A processor rather than anything structlog provides. Its own context
    handling is thread local in this version and a per-request id wants to be
    cleared explicitly at the end of the request, which is easier to reason
    about when the dictionary is in plain sight.
    """
    for key, value in _CONTEXT.fields.items():
        event.setdefault(key, value)
    return event
