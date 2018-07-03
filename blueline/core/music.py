"""Which rows sound good, and how to count them.

Composers do not only care that a touch is true. Some rows are worth having and
a composition that produces plenty of them is worth more than one that does
not, so anything that judges compositions has to be able to count them.

The named rows are the ones every ringer knows by ear. Queens is the odd bells
followed by the even ones, tittums has the two halves of the ring interleaved
so it sounds like a peal of two rings at once, and backrounds is the whole
thing upside down. Runs matter more in practice: four or more bells coming down
in order at the back is the thing most compositions are actually chasing.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from collections import Counter
from dataclasses import dataclass

from blueline.core.row import Row


def _consecutive_run(bells: Tuple[int, ...]) -> bool:
    """Whether these bells go up or down one at a time with no gaps."""
    if len(bells) < 2:
        return False
    steps = {later - earlier for earlier, later in zip(bells, bells[1:])}
    return steps in ({1}, {-1})


def run_at_back(row: Row, length: int) -> bool:
    """Whether the last few bells run in order, up or down."""
    if length < 2 or length > row.stage:
        return False
    return _consecutive_run(row.bells[-length:])


def run_at_front(row: Row, length: int) -> bool:
    """Whether the first few bells run in order, up or down."""
    if length < 2 or length > row.stage:
        return False
    return _consecutive_run(row.bells[:length])


def longest_run_at_back(row: Row) -> int:
    """The longest run ending at the back, or nought if there is none."""
    for length in range(row.stage, 1, -1):
        if run_at_back(row, length):
            return length
    return 0


def longest_run_at_front(row: Row) -> int:
    for length in range(row.stage, 1, -1):
        if run_at_front(row, length):
            return length
    return 0


def queens(stage: int) -> Row:
    """The odd bells and then the even ones, which is 13572468 at major."""
    odds = [bell for bell in range(1, stage + 1) if bell % 2 == 1]
    evens = [bell for bell in range(1, stage + 1) if bell % 2 == 0]
    return Row(tuple(odds + evens))


def kings(stage: int) -> Row:
    """Queens with the odd bells turned round, so 75312468 at major."""
    odds = [bell for bell in range(1, stage + 1) if bell % 2 == 1]
    evens = [bell for bell in range(1, stage + 1) if bell % 2 == 0]
    return Row(tuple(list(reversed(odds)) + evens))


def tittums(stage: int) -> Row:
    """The two halves of the ring interleaved, 15263748 at major.

    On an odd stage the front half is the longer one, which is what falls out
    of dealing the bells alternately from each end of the two halves.
    """
    half = (stage + 1) // 2
    front = list(range(1, half + 1))
    back = list(range(half + 1, stage + 1))
    out: List[int] = []
    for index in range(half):
        out.append(front[index])
        if index < len(back):
            out.append(back[index])
    return Row(tuple(out))


def backrounds(stage: int) -> Row:
    """The whole ring upside down."""
    return Row(tuple(range(stage, 0, -1)))


NAMED_ROWS = {
    "rounds": Row.rounds,
    "backrounds": backrounds,
    "queens": queens,
    "kings": kings,
    "tittums": tittums,
}


def name_of(row: Row) -> Optional[str]:
    """What ringers call this row, if they call it anything."""
    for name, make in NAMED_ROWS.items():
        if make(row.stage) == row:
            return name
    return None


@dataclass(frozen=True)
class MusicCount:
    """What music a run of rows contains."""

    named: Counter[str]
    runs_at_back: Counter[int]
    runs_at_front: Counter[int]

    @property
    def total_named(self) -> int:
        return sum(self.named.values())

    def runs_of_at_least(self, length: int, at_back: bool = True) -> int:
        counts = self.runs_at_back if at_back else self.runs_at_front
        return sum(count for run, count in counts.items() if run >= length)


def count_music(rows: List[Row], min_run: int = 4) -> MusicCount:
    """Go through some rows and total up what is worth hearing.

    Only the longest run in each row is counted. A row ending 5678 also ends
    678 and 78, and counting all three would make one good row look like three.
    """
    named: Counter[str] = Counter()
    back: Counter[int] = Counter()
    front: Counter[int] = Counter()
    for row in rows:
        name = name_of(row)
        if name is not None:
            named[name] += 1
        longest_back = longest_run_at_back(row)
        if longest_back >= min_run:
            back[longest_back] += 1
        longest_front = longest_run_at_front(row)
        if longest_front >= min_run:
            front[longest_front] += 1
    return MusicCount(named=named, runs_at_back=back, runs_at_front=front)
