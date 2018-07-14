"""Falseness between courses, which is what limits a composition.

A method's plain course is usually true against itself. What matters to a
composer is whether it stays true against the same course started from a
different row, because a composition is built out of courses and if two of them
clash they cannot both be in it.

The rows a course can be started from are its course heads. A course head that
produces a clash is a false course head, and the set of them is fixed for the
method: work them out once and a composer can tell at a glance which courses
may be used together. This is the single most useful thing to know about a
Surprise method beyond its line.

Working them out is a matter of taking every row of the course, transposing the
course by it, and seeing whether anything lands on top of anything else. That
is O(course squared) and the courses are short, so nothing clever is needed.
"""

from __future__ import annotations

from typing import List, Set

from collections import Counter
from dataclasses import dataclass

from blueline.core.method import Method
from blueline.core.row import Row
from blueline.core.touch import plain_course


@dataclass(frozen=True)
class FalseCourseHead:
    """A course head that clashes with the plain course, and how badly."""

    head: Row
    #: How many rows the two courses have in common.
    clashes: int

    def __str__(self) -> str:
        return f"{self.head} ({self.clashes})"


def course_rows(method: Method) -> List[Row]:
    """Every row of the plain course, without the closing rounds."""
    return plain_course(method).rows()[:-1]


def transposed_course(rows: List[Row], head: Row) -> List[Row]:
    """The same course started from a different row."""
    return [row.transposed_by(head) for row in rows]


def clashes_between(first: List[Row], second: List[Row]) -> int:
    """How many rows two courses have in common."""
    return len(set(first) & set(second))


def head_taking(first: Row, second: Row) -> Row:
    """The course head that carries one row on to another.

    If a course starting from rounds has a row here, then a course starting
    from this head has that same row where the other one was. That is the whole
    of falseness in one line.
    """
    return first.inverse.transposed_by(second)


def false_course_heads(method: Method, hunt_fixed: bool = True) -> List[FalseCourseHead]:
    """Every course head that cannot be rung alongside the plain course.

    Worked out from pairs rather than by trying every row at the stage. For
    each pair of rows in the course there is exactly one head that lands the
    first on the second, and collecting those gives the answer directly. At
    major that is fifty thousand pairs instead of a million transpositions.

    Rounds is left out. The plain course clashes with itself completely, which
    is a fact about arithmetic rather than about the method.
    """
    rows = course_rows(method)
    hunting = method.hunt_bells
    tally: Counter[Row] = Counter()
    for first in rows:
        inverse = first.inverse
        for second in rows:
            head = inverse.transposed_by(second)
            if head.is_rounds:
                continue
            tally[head] += 1

    found = [
        FalseCourseHead(head=head, clashes=clashes)
        for head, clashes in tally.items()
        if not hunt_fixed or all(head[bell] == bell for bell in hunting)
    ]
    return sorted(found, key=lambda entry: (-entry.clashes, str(entry.head)))


def false_course_head_rows(method: Method) -> List[Row]:
    """Just the heads, for feeding straight back into a truth check."""
    return [entry.head for entry in false_course_heads(method)]


def is_true_against(method: Method, heads: List[Row]) -> bool:
    """Whether a set of courses can all be rung together."""
    rows = course_rows(method)
    seen: Set[Row] = set()
    for head in heads:
        for row in rows:
            moved = row.transposed_by(head)
            if moved in seen:
                return False
            seen.add(moved)
    return True


def tenors_together_heads(method: Method) -> List[Row]:
    """Course heads that leave the back two bells alone.

    Most compositions of major keep the tenors together because a course where
    they split sounds worse and is harder to ring, so a composer wants to know
    which of the false heads fall inside that set and which can be ignored.
    """
    stage = method.stage
    if stage < 4:
        return []
    return [
        entry.head
        for entry in false_course_heads(method)
        if entry.head[stage] == stage and entry.head[stage - 1] == stage - 1
    ]
