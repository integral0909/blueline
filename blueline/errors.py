"""Everything this library refuses to do, and why.

Nine modules had each grown an error class of their own, all deriving straight
from ValueError and none of them related to each other. That was fine while
they stayed in core, and stopped being fine the moment an api handler wanted to
turn a bad request into a sensible response: catching nine unrelated types and
hoping none had been missed is not a plan.

They all hang off BluelineError now, so a caller can catch the lot in one go
and still pick out the particular one when it matters. The names have not
changed, because they read well at the point they are raised.
"""

from __future__ import annotations


class BluelineError(ValueError):
    """Anything this library refuses.

    Derives from ValueError so existing callers catching that keep working.
    """


class StageError(BluelineError):
    """A stage outside the range this library can work with."""


class RowError(BluelineError):
    """A row that is not a permutation of the bells at its stage."""


class NotationError(BluelineError):
    """Place notation that cannot be read, or that does not work at its stage."""


class MethodError(BluelineError):
    """A method that does not hold together."""


class CallError(BluelineError):
    """A call that does not fit the method it is being called in."""


class TouchError(BluelineError):
    """A touch that cannot be rung as written."""


class CoursingError(BluelineError):
    """A method whose coursing order does not mean anything."""


class TitleError(BluelineError):
    """A title that cannot be read, or one that could not be built."""


class LibraryError(BluelineError):
    """A method that cannot go in the library, or one that is not in it."""


__all__ = [
    "BluelineError",
    "CallError",
    "CoursingError",
    "LibraryError",
    "MethodError",
    "NotationError",
    "RowError",
    "StageError",
    "TitleError",
    "TouchError",
]
