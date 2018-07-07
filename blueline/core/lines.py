"""Drawing the blue line, which is how anybody learns a method.

A ringer does not learn a method from its place notation. They learn the path
one bell takes through a lead, drawn as a line down the page, and that line is
what the whole library is named after. Everything here turns rows into
something that can be drawn or printed.

A grid is the rows written out one per line with the bells in columns. Marking
a bell means picking out its place in each row so the eye can follow it down,
and the places where the line stops and turns are what a ringer actually
memorises, so those get named separately.
"""

from __future__ import annotations

from typing import List, Tuple

from dataclasses import dataclass

from blueline.core.method import Method
from blueline.core.row import Row
from blueline.core.stage import bell_symbol


@dataclass(frozen=True)
class Segment:
    """A stretch of a bell's line that goes one way without turning."""

    start_row: int
    end_row: int
    start_place: int
    end_place: int

    @property
    def blows(self) -> int:
        """How many blows the bell strikes over this stretch.

        A bell standing in one place across rows four and five has struck two
        blows there, not one, so this counts rows rather than gaps.
        """
        return self.end_row - self.start_row + 1

    @property
    def is_still(self) -> bool:
        """Whether the bell stayed in the same place, making places."""
        return self.start_place == self.end_place

    @property
    def going_up(self) -> bool:
        return self.end_place > self.start_place

    def __str__(self) -> str:
        if self.is_still:
            return f"{self.blows} blows in {self.start_place}"
        way = "up" if self.going_up else "down"
        return f"{self.start_place} to {self.end_place} {way}"


def path_segments(path: Tuple[int, ...]) -> List[Segment]:
    """Break a bell's path into the runs a ringer would describe it in.

    Hunting up counts as one segment however far it goes, and a pair of blows
    in the same place is another. This is the difference between reading a line
    as nine separate numbers and reading it as hunt up, make seconds, hunt down.
    """
    if len(path) < 2:
        return []
    segments: List[Segment] = []
    start = 0
    direction = path[1] - path[0]
    for index in range(1, len(path)):
        step = path[index] - path[index - 1]
        if step != direction:
            segments.append(
                Segment(
                    start_row=start,
                    end_row=index - 1,
                    start_place=path[start],
                    end_place=path[index - 1],
                )
            )
            start = index - 1
            direction = step
    segments.append(
        Segment(
            start_row=start,
            end_row=len(path) - 1,
            start_place=path[start],
            end_place=path[-1],
        )
    )
    return segments


def describe_path(path: Tuple[int, ...]) -> str:
    """A bell's work through a lead, in words."""
    parts = [str(segment) for segment in path_segments(path)]
    return ", ".join(parts) if parts else "nothing"


def grid(rows: List[Row]) -> List[str]:
    """The rows written out one per line."""
    return [str(row) for row in rows]


def marked_grid(rows: List[Row], bell: int, mark: str = "*") -> List[str]:
    """The grid with one bell picked out, so its line can be followed."""
    if len(mark) != 1:
        raise ValueError("a mark has to be a single character")
    out: List[str] = []
    for row in rows:
        place = row.place_of(bell)
        chars = [bell_symbol(each) for each in row.bells]
        chars[place - 1] = mark
        out.append("".join(chars))
    return out


def line_of(method: Method, bell: int) -> List[int]:
    """Where a bell rings in each row of a lead, as places."""
    return list(method.path_of(bell))


def leads_of_course(method: Method) -> List[List[Row]]:
    """The plain course broken back into its leads."""
    out: List[List[Row]] = []
    row = Row.rounds(method.stage)
    for _ in range(method.leads_in_course):
        lead = method.lead_rows(row)
        out.append(lead)
        row = lead[-1]
    return out


def place_bell_order(method: Method) -> List[int]:
    """Which place bell a working bell becomes at each lead head.

    A bell that starts a lead in third place is the third place bell, and
    knowing which one you turn into next is how ringers keep their place
    through a course without counting rows.
    """
    head = method.lead_head
    order: List[int] = []
    place = 2
    for _ in range(method.leads_in_course):
        order.append(place)
        place = head.place_of(place)
    return order
