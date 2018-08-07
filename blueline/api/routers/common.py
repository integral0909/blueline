"""What every router needs.

What a router does with a result: the status table and the unwrap helper.
What a router is given lives in api.stores instead, because the two grew
together in here and this was on its way to holding everything.
"""

from __future__ import annotations

from typing import Dict, TypeVar

from blueline.api.wsgi import HttpError
from blueline.service.results import Failure, Reason, Result

T = TypeVar("T")

#: One place that decides what a refusal means over http.
STATUS_FOR: Dict[Reason, int] = {
    Reason.NOT_FOUND: 404,
    Reason.ALREADY_EXISTS: 409,
    Reason.INVALID: 422,
}


def refuse(failure: Failure) -> HttpError:
    return HttpError(STATUS_FOR[failure.reason], failure.reason.value, failure.detail)


def unwrap(result: Result[T]) -> T:
    """The value, or the right http error."""
    if result.failure is not None:
        raise refuse(result.failure)
    return result.unwrap()
