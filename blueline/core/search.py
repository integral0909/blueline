"""Looking for touches that come round and are true.

A composer does not write a calling and hope. They decide how long they want,
which calls they are willing to use and where, and then look for the callings
that work. That search is what this does: walk the tree of callings lead by
lead, throw away anything that has already gone false, and keep what comes
round at an acceptable length.

Pruning early is the whole trick. A calling that repeats a row at the third
lead cannot be rescued by anything called later, so the branch is dropped
rather than expanded. Without that, even a modest search at minor is
unfinishable.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from dataclasses import dataclass, field

from blueline.core.calls import Call, called_lead
from blueline.core.method import Method
from blueline.core.row import Row


@dataclass(frozen=True)
class Found:
    """A calling that came round, and what it came to."""

    calling: str
    leads: int
    length: int

    def __str__(self) -> str:
        return f"{self.calling} ({self.length})"


@dataclass()
class Limits:
    """What the composer will accept."""

    min_length: int = 1
    max_length: int = 5040
    max_leads: int = 60
    #: Stop after this many, so a wide search still answers.
    max_found: int = 20
    #: Give up after looking at this many callings, whatever happens.
    max_nodes: int = 200_000

    def wants(self, length: int) -> bool:
        return self.min_length <= length <= self.max_length


@dataclass()
class _Walk:
    """What the search is carrying as it goes."""

    found: List[Found] = field(default_factory=list)
    nodes: int = 0
    exhausted: bool = True


def search_callings(
    method: Method,
    calls: Dict[str, Call],
    limits: Optional[Limits] = None,
    allowed: Optional[str] = None,
) -> Tuple[List[Found], bool]:
    """Every calling that comes round true, within the limits.

    Gives back what was found and whether the search finished. A search that
    stopped early because it hit a cap has not proved anything about what it
    did not look at, and saying so is more use than quietly returning less.
    """
    bounds = limits or Limits()
    symbols = list(allowed) if allowed else ["p", *sorted(calls)]
    lead_length = method.lead_length
    rounds = Row.rounds(method.stage)
    walk = _Walk()

    def step(row: Row, rung: Set[Row], calling: List[str]) -> None:
        if len(walk.found) >= bounds.max_found or walk.nodes >= bounds.max_nodes:
            walk.exhausted = False
            return
        if len(calling) >= bounds.max_leads:
            return

        for symbol in symbols:
            walk.nodes += 1
            call = None if symbol == "p" else calls.get(symbol)
            if symbol != "p" and call is None:
                continue

            lead = called_lead(method.changes, call, row)
            body = lead[:-1]
            if any(each in rung for each in body):
                continue

            calling.append(symbol)
            length = len(calling) * lead_length
            head = lead[-1]

            if head.is_rounds:
                if bounds.wants(length):
                    walk.found.append(
                        Found(calling="".join(calling), leads=len(calling), length=length)
                    )
            elif length < bounds.max_length:
                step(head, rung | set(body), calling)

            calling.pop()
            if len(walk.found) >= bounds.max_found:
                walk.exhausted = False
                return

    step(rounds, set(), [])
    walk.found.sort(key=lambda entry: (entry.length, entry.calling))
    return walk.found, walk.exhausted


def shortest_touch(
    method: Method,
    calls: Dict[str, Call],
    min_length: int = 1,
) -> Optional[Found]:
    """The shortest true touch of at least a given length, or nothing."""
    found, _ = search_callings(
        method,
        calls,
        Limits(min_length=min_length, max_found=1, max_leads=30),
    )
    return found[0] if found else None
