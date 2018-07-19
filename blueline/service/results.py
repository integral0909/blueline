"""How a service call reports what happened.

Handlers need to tell three things apart: it worked, the caller asked for
something that is not there, and the caller asked for something that does not
make sense. Raising for the last two and returning for the first means every
call site is a try block, and the http layer ends up mapping exception types to
status codes in a long chain nobody enjoys reading.

A result carries the outcome instead. The api turns a reason into a status code
in one place and the cli prints it, and neither has to know what the other does
with it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class Reason(str, Enum):
    """Why a call did not do what was asked."""

    NOT_FOUND = "not-found"
    ALREADY_EXISTS = "already-exists"
    INVALID = "invalid"


@dataclass(frozen=True)
class Failure:
    reason: Reason
    detail: str

    def __str__(self) -> str:
        return self.detail


@dataclass(frozen=True)
class Result(Generic[T]):
    """What a service call gives back, worked or not."""

    value: Optional[T] = None
    failure: Optional[Failure] = None

    @property
    def ok(self) -> bool:
        return self.failure is None

    def unwrap(self) -> T:
        """The value, for a caller that has already checked."""
        if self.failure is not None:
            raise ValueError(f"unwrapped a failed result: {self.failure.detail}")
        # A successful result always carries a value; None is only ever a failure.
        return self.value  # type: ignore[return-value]


def succeeded(value: T) -> Result[T]:
    return Result(value=value)


def not_found(detail: str) -> Result[T]:
    return Result(failure=Failure(Reason.NOT_FOUND, detail))


def already_exists(detail: str) -> Result[T]:
    return Result(failure=Failure(Reason.ALREADY_EXISTS, detail))


def invalid(detail: str) -> Result[T]:
    return Result(failure=Failure(Reason.INVALID, detail))
