"""Rendering a peal board, which is the point of recording anything.

A performance in a database is a row. A peal board is what goes on the wall:
the tower at the top, the date, what was rung and how long it took, then the
band in bell order with the conductor marked. The layout is not decoration.
Every board in the country reads the same way and a ringer looking at one
knows where to find each part without reading it.

The width matters too. Boards are painted to a width and the text is centred
in it, so anything producing one has to know how wide it is going to be rather
than leaving it to whatever is displaying it.
"""

from __future__ import annotations

from typing import List, Tuple

from dataclasses import dataclass

from blueline.core.performance import Performance
from blueline.errors import BluelineError

#: How wide a board is, in characters. Wide enough for a long method title and
#: a name beside a bell number, and narrow enough to read in one go.
WIDTH = 44


class BoardError(BluelineError):
    """A board that cannot be laid out."""


@dataclass(frozen=True)
class Board:
    """A peal board, laid out."""

    lines: Tuple[str, ...]
    width: int

    def __str__(self) -> str:
        return "\n".join(self.lines)

    @property
    def height(self) -> int:
        return len(self.lines)


def centred(text: str, width: int = WIDTH) -> str:
    """Text in the middle of a line, trimmed rather than overflowing.

    A name too long for the board is cut rather than wrapped. A board is a
    fixed shape and a line that ran on would push everything below it down.

    Runs of space are collapsed, so anything wanting two spaces between two
    words will not get them. Nothing on a board needs them.
    """
    if width < 1:
        raise BoardError("a board has to have some width")
    cleaned = " ".join(text.split())
    if len(cleaned) > width:
        cleaned = cleaned[: width - 1].rstrip() + "…"
    return cleaned.center(width)


def rule(width: int = WIDTH, character: str = "-") -> str:
    if len(character) != 1:
        raise BoardError("a rule is drawn with one character")
    return character * width


def band_lines(performance: Performance, width: int = WIDTH) -> List[str]:
    """The band, one to a line, bell number and name."""
    from blueline.core.stage import bell_symbol

    out: List[str] = []
    for bell, name in enumerate(performance.band.ringers, start=1):
        mark = " (c)" if bell == performance.band.conductor else ""
        out.append(centred(f"{bell_symbol(bell)} {name.strip()}{mark}", width))
    return out


def render(performance: Performance, width: int = WIDTH) -> Board:
    """A performance as it would be painted."""
    standing = performance.standing.counts_as
    lines = [
        centred(performance.place, width),
        centred(f"{performance.rang_on:%d %B %Y}", width),
        rule(width),
        centred(f"A {standing} of {performance.length} changes", width),
        centred(performance.title, width),
        centred(_took(performance), width),
    ]
    if performance.composer:
        lines.append(centred(f"Composed by {performance.composer}", width))
    lines.append(rule(width))
    lines.extend(band_lines(performance, width))
    if performance.has_covering_tenor:
        lines.append(centred(f"{performance.band.stage} covering", width))
    return Board(lines=tuple(lines), width=width)


def _took(performance: Performance) -> str:
    total = int(round(performance.duration.total_seconds() / 60))
    hours, minutes = divmod(total, 60)
    if not hours:
        return f"in {minutes} minutes"
    return f"in {hours}h {minutes:02d}m"
