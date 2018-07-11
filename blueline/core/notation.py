"""Place notation, which is how a method is written down.

A change says which bells stay where they are and lets the rest swap with a
neighbour. Ringers write the places that are made and leave the swapping
implied, so 16 at minor means the treble and the tenor stay put while the four
bells in between change over in pairs. A change where nobody makes a place is
written x, or a dash, and only exists at even stages because an odd number of
bells cannot pair up.

Two things make this fiddly enough to want its own module. Places at the very
top and bottom are often left out, because a notation like 3 at minor can only
possibly mean 36, and readers are expected to work that out. And most methods
are palindromic, so they are written as half a lead and a comma and a lead end
change, which has to be unfolded before it means anything.
"""

from __future__ import annotations

from typing import List, Tuple

from dataclasses import dataclass

from blueline.core.row import Row
from blueline.core.stage import bell_number, bell_symbol, check_stage
from blueline.errors import NotationError

CROSS_SYMBOLS = "-x"
SEPARATORS = ".&"


@dataclass(frozen=True)
class Change:
    """One change, held as the places that are made."""

    places: Tuple[int, ...]
    stage: int

    def __post_init__(self) -> None:
        check_stage(self.stage)
        if list(self.places) != sorted(set(self.places)):
            raise NotationError(f"places {self.places} are repeated or out of order")
        for place in self.places:
            if place < 1 or place > self.stage:
                raise NotationError(f"no place {place} at stage {self.stage}")
        self._check_pairs()

    def _check_pairs(self) -> None:
        """Every run of bells that is not making a place has to pair up."""
        edges = [0, *self.places, self.stage + 1]
        for lower, upper in zip(edges, edges[1:]):
            if (upper - lower - 1) % 2 != 0:
                raise NotationError(
                    f"{self!s} leaves an odd number of bells between "
                    f"places {lower} and {upper} at stage {self.stage}"
                )

    @property
    def is_cross(self) -> bool:
        return not self.places

    def __str__(self) -> str:
        if self.is_cross:
            return "x"
        return "".join(bell_symbol(place) for place in self.places)

    def __repr__(self) -> str:
        return f"Change({str(self)!r}, stage={self.stage})"

    def apply(self, row: Row) -> Row:
        """The row that follows this one, once this change has been made."""
        if row.stage != self.stage:
            raise NotationError(f"cannot apply a stage {self.stage} change to {row}")
        made = set(self.places)
        bells = list(row.bells)
        place = 1
        while place < self.stage:
            if place in made:
                place += 1
                continue
            bells[place - 1], bells[place] = bells[place], bells[place - 1]
            place += 2
        return Row(tuple(bells))


def implied_places(places: List[int], stage: int) -> Tuple[int, ...]:
    """Put back the places at the top and bottom that writers leave out.

    A gap with an odd number of bells in it cannot pair up, and the only place
    a reader is allowed to add one is at an end. An odd gap in the middle is a
    notation that does not work rather than one with something missing.
    """
    made = sorted(set(places))
    if made and (made[0] - 1) % 2 == 1:
        made.insert(0, 1)
    if made and (stage - made[-1]) % 2 == 1:
        made.append(stage)
    if not made and stage % 2 == 1:
        raise NotationError(f"a cross change needs an even stage, not {stage}")
    return tuple(made)


def parse_change(token: str, stage: int) -> Change:
    """Read one change, such as 16 or x."""
    cleaned = token.strip()
    if not cleaned:
        raise NotationError("an empty change")
    if cleaned in CROSS_SYMBOLS:
        return Change(implied_places([], stage), stage)
    places = [bell_number(char) for char in cleaned]
    return Change(implied_places(places, stage), stage)


def split_changes(text: str) -> List[str]:
    """Break notation into its changes, coping with dots and bare crosses."""
    tokens: List[str] = []
    current = ""
    for char in text:
        if char in SEPARATORS:
            if current:
                tokens.append(current)
                current = ""
            continue
        if char in CROSS_SYMBOLS:
            if current:
                tokens.append(current)
                current = ""
            tokens.append("x")
            continue
        current += char
    if current:
        tokens.append(current)
    return tokens


def expand_symmetric(half: List[Change], lead_end: List[Change]) -> List[Change]:
    """Unfold notation written as half a lead, a comma and a lead end.

    The half runs down to and including the half lead change, then comes back
    up the way it went without repeating that change, and the lead end is
    tacked on the end.
    """
    if not half:
        raise NotationError("nothing before the comma")
    return [*half, *reversed(half[:-1]), *lead_end]


def parse_notation(text: str, stage: int) -> List[Change]:
    """Read a whole method's notation, symmetric or written out in full."""
    check_stage(stage)
    cleaned = text.strip()
    if not cleaned:
        raise NotationError("empty notation")
    parts = cleaned.split(",")
    if len(parts) == 1:
        return [parse_change(token, stage) for token in split_changes(parts[0])]
    if len(parts) != 2:
        raise NotationError("notation can only have one comma in it")
    half = [parse_change(token, stage) for token in split_changes(parts[0])]
    lead_end = [parse_change(token, stage) for token in split_changes(parts[1])]
    return expand_symmetric(half, lead_end)


def format_notation(changes: List[Change]) -> str:
    """Write changes back out, putting dots only where they are needed.

    A cross separates the changes either side of it well enough on its own, so
    a dot next to one is noise.
    """
    out = ""
    previous_was_places = False
    for change in changes:
        text = str(change)
        if change.is_cross:
            out += text
            previous_was_places = False
            continue
        if previous_was_places:
            out += "."
        out += text
        previous_was_places = True
    return out


def apply_all(changes: List[Change], start: Row) -> List[Row]:
    """Ring the changes from a starting row, giving every row along the way."""
    rows = [start]
    row = start
    for change in changes:
        row = change.apply(row)
        rows.append(row)
    return rows
