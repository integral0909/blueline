"""What every reader hands back.

Both readers had grown the same result type, with the same three methods on it,
and the service had to know which one it was looking at to catch the right
error. There is only one shape here: what was read, and what could not be.

The rule both readers follow is that one bad method does not throw the file
away. Somebody importing forty methods wants the thirty nine that are fine and
a list of what to fix, not a refusal.
"""

from __future__ import annotations

from typing import List

from dataclasses import dataclass, field

from blueline.core.method import Method
from blueline.errors import BluelineError


class LoadError(BluelineError):
    """A file that cannot be read as a collection of methods at all.

    Distinct from a method inside it that will not parse. This is the file
    being the wrong thing: not json, not xml, a json array where an object
    belongs.
    """


@dataclass()
class LoadResult:
    """What came out of a file, and what would not."""

    methods: List[Method] = field(default_factory=list)
    problems: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def __len__(self) -> int:
        return len(self.methods)

    def summary(self) -> str:
        if self.ok:
            return f"{len(self.methods)} methods"
        return f"{len(self.methods)} methods, {len(self.problems)} could not be read"

    def named(self) -> List[str]:
        """The names of what was read, for a caller reporting on the import."""
        return [method.name for method in self.methods]
