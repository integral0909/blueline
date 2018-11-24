"""What two methods have in common, and where they part company.

The way anybody actually learns a new method is against one they already ring.
Yorkshire is Cambridge with the places moved, Superlative has the same front
work and different back work, and a teacher explaining either of them starts
from what the band already knows.

So the useful comparison is not a character diff of the notation. It is: how
much of the lead is the same, where does it stop being the same, and does the
new one course the same way, because a method with the same lead head takes the
same compositions and a band can call what it already calls.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from dataclasses import dataclass

from blueline.core.method import Method
from blueline.core.notation import format_notation
from blueline.errors import BluelineError


class CompareError(BluelineError):
    """Two methods that cannot usefully be compared."""


@dataclass(frozen=True)
class Divergence:
    """One place two methods stop agreeing."""

    at: int
    left: str
    right: str

    def __str__(self) -> str:
        return f"change {self.at}: {self.left} against {self.right}"


@dataclass(frozen=True)
class Comparison:
    """How alike two methods are."""

    left: str
    right: str
    changes: int
    same: int
    divergences: Tuple[Divergence, ...]
    same_lead_head: bool
    same_length: bool

    @property
    def share(self) -> float:
        """How much of the lead is identical."""
        return self.same / self.changes if self.changes else 1.0

    @property
    def first_difference(self) -> Optional[Divergence]:
        return self.divergences[0] if self.divergences else None

    @property
    def identical(self) -> bool:
        return not self.divergences and self.same_length

    def summary(self) -> str:
        if self.identical:
            return f"{self.left} and {self.right} are the same method"
        if not self.same_length:
            return f"{self.left} and {self.right} have leads of different lengths"
        return (
            f"{self.left} and {self.right} agree on {self.same} of "
            f"{self.changes} changes, {self.share:.0%}"
        )


def compare(left: Method, right: Method) -> Comparison:
    """How alike two methods are, change by change.

    Compared change by change rather than row by row. Two methods can pass
    through the same row by different routes, and a ringer learning one against
    the other cares about what they do, not where they happen to be.
    """
    if left.stage != right.stage:
        raise CompareError(f"{left.name} is at {left.stage} and {right.name} at {right.stage}")

    together = min(len(left.changes), len(right.changes))
    divergences: List[Divergence] = []
    same = 0
    for index in range(together):
        one, other = left.changes[index], right.changes[index]
        if one == other:
            same += 1
            continue
        divergences.append(
            Divergence(
                at=index + 1,
                left=format_notation([one]),
                right=format_notation([other]),
            )
        )

    # A lead that runs on past the other is not "the same so far and then
    # different". Every change past the shorter one is a difference, and a
    # comparison that quietly ignored them would say Cambridge Minor and
    # Cambridge Major mostly agree.
    for index in range(together, max(len(left.changes), len(right.changes))):
        longer, which = (
            (left, "left") if len(left.changes) > len(right.changes) else (right, "right")
        )
        extra = format_notation([longer.changes[index]])
        divergences.append(
            Divergence(
                at=index + 1,
                left=extra if which == "left" else "",
                right=extra if which == "right" else "",
            )
        )

    return Comparison(
        left=left.name,
        right=right.name,
        changes=max(len(left.changes), len(right.changes)),
        same=same,
        divergences=tuple(divergences),
        same_lead_head=left.lead_head == right.lead_head,
        same_length=len(left.changes) == len(right.changes),
    )


def shared_work(left: Method, right: Method, bell: int) -> int:
    """How many blows one bell strikes in the same place in both.

    Answered for one bell because that is the question a learner asks: I ring
    the three in Cambridge, what does the three do here.
    """
    if left.stage != right.stage:
        raise CompareError("both methods have to be at the same stage")
    one = left.path_of(bell)[:-1]
    other = right.path_of(bell)[:-1]
    return sum(1 for a, b in zip(one, other) if a == b)


def most_alike(wanted: Method, among: List[Method]) -> Optional[Method]:
    """Whichever of a set a method is most like.

    What a teacher reaches for: this is nearly Yorkshire, ring it like that
    and watch the back work. Anything at a different stage is not a candidate
    rather than an error, because a library has every stage in it.
    """
    candidates = [
        method
        for method in among
        if method.stage == wanted.stage and method.changes != wanted.changes
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda method: compare(wanted, method).share)
