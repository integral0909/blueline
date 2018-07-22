"""Checking what came in, in place of a schema library.

pydantic did the declaring and the checking together, and taking it out means
the checking has to be written down. That is less magic and more lines, which
for sixty endpoints reading about four values each is a fair trade: what a
field is allowed to be is now readable at the point it is read.

Everything raises HttpError with a 422 and a sentence, so a caller gets the
same shape of refusal from a bad query string as from a bad body.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, overload

from blueline.api.wsgi import HttpError

MISSING = object()


def fail(detail: str) -> HttpError:
    return HttpError(422, "invalid", detail)


def body_of(request: Any) -> Dict[str, Any]:
    """The request body, which has to be an object."""
    found = request.json()
    if found is None:
        raise fail("this needs a json body")
    if not isinstance(found, dict):
        raise fail("the body has to be an object")
    return found


def text(
    source: Dict[str, Any],
    name: str,
    default: Any = MISSING,
    least: int = 0,
    most: int = 10_000,
    strip: bool = True,
) -> str:
    value = source.get(name, default)
    if value is MISSING:
        raise fail(f"{name} is needed")
    if value is None and default is None:
        return ""
    if not isinstance(value, str):
        raise fail(f"{name} has to be text")
    if strip:
        value = value.strip()
    if len(value) < least:
        raise fail(f"{name} cannot be blank" if least == 1 else f"{name} is too short")
    if len(value) > most:
        raise fail(f"{name} is longer than {most} characters")
    return value


def whole(
    source: Dict[str, Any],
    name: str,
    default: Any = MISSING,
    least: Optional[int] = None,
    most: Optional[int] = None,
) -> int:
    value = source.get(name, default)
    if value is MISSING:
        raise fail(f"{name} is needed")
    if isinstance(value, bool) or not isinstance(value, int):
        try:
            value = int(str(value))
        except (TypeError, ValueError):
            raise fail(f"{name} has to be a whole number")
    if least is not None and value < least:
        raise fail(f"{name} has to be at least {least}")
    if most is not None and value > most:
        raise fail(f"{name} cannot be more than {most}")
    return value


def number(
    source: Dict[str, Any],
    name: str,
    default: Any = MISSING,
    least: Optional[float] = None,
    most: Optional[float] = None,
) -> float:
    value = source.get(name, default)
    if value is MISSING:
        raise fail(f"{name} is needed")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise fail(f"{name} has to be a number")
    if least is not None and value < least:
        raise fail(f"{name} has to be at least {least}")
    if most is not None and value > most:
        raise fail(f"{name} cannot be more than {most}")
    return value


def flag(source: Dict[str, Any], name: str, default: bool = False) -> bool:
    value = source.get(name, MISSING)
    if value is MISSING:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def listing(
    source: Dict[str, Any],
    name: str,
    default: Any = MISSING,
    least: int = 0,
    most: int = 1000,
) -> List[Any]:
    value = source.get(name, default)
    if value is MISSING:
        raise fail(f"{name} is needed")
    if value is None:
        return []
    if not isinstance(value, list):
        raise fail(f"{name} has to be a list")
    if len(value) < least:
        raise fail(f"{name} needs at least {least}")
    if len(value) > most:
        raise fail(f"{name} cannot have more than {most}")
    return value


def one_of(value: str, allowed: Sequence[str], name: str) -> str:
    if value not in allowed:
        raise fail(f"{name} has to be one of {', '.join(allowed)}")
    return value


@overload
def query_text(request: Any, name: str, default: str, most: int = ...) -> str:
    ...


@overload
def query_text(
    request: Any, name: str, default: None = ..., most: int = ...
) -> Optional[str]:
    ...


def query_text(
    request: Any, name: str, default: Optional[str] = None, most: int = 10_000
) -> Optional[str]:
    value = request.query(name, default)
    if value is None:
        return None
    if len(value) > most:
        raise fail(f"{name} is longer than {most} characters")
    return value


@overload
def query_whole(
    request: Any,
    name: str,
    default: int,
    least: Optional[int] = ...,
    most: Optional[int] = ...,
) -> int:
    ...


@overload
def query_whole(
    request: Any,
    name: str,
    default: None = ...,
    least: Optional[int] = ...,
    most: Optional[int] = ...,
) -> Optional[int]:
    ...


def query_whole(
    request: Any,
    name: str,
    default: Optional[int] = None,
    least: Optional[int] = None,
    most: Optional[int] = None,
) -> Optional[int]:
    """A whole number from the query string.

    Two signatures: given a default it always gives back a number, and
    without one it may give back nothing. Saying so means a caller passing a
    default does not have to check for None it can never get.
    """
    raw = request.query(name)
    if raw is None:
        return default
    return whole({name: raw}, name, least=least, most=most)


@overload
def query_number(
    request: Any,
    name: str,
    default: float,
    least: Optional[float] = ...,
    most: Optional[float] = ...,
) -> float:
    ...


@overload
def query_number(
    request: Any,
    name: str,
    default: None = ...,
    least: Optional[float] = ...,
    most: Optional[float] = ...,
) -> Optional[float]:
    ...


def query_number(
    request: Any,
    name: str,
    default: Optional[float] = None,
    least: Optional[float] = None,
    most: Optional[float] = None,
) -> Optional[float]:
    raw = request.query(name)
    if raw is None:
        return default
    return number({name: raw}, name, least=least, most=most)


def query_flag(request: Any, name: str, default: bool = False) -> bool:
    raw = request.query(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def path_whole(value: str, name: str) -> int:
    """A number out of the path, which is a 404 rather than a 422.

    /performances/totals reaching the handler for /performances/{id} means the
    caller asked for something that is not there, not that they sent a bad
    number.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        raise HttpError(404, "not-found", f"no {name} called {value!r}")
