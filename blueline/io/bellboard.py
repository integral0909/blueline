"""Writing a performance up the way it gets submitted.

Peals and quarters get posted to a performance site, and the format everybody
pastes in is the one a report in The Ringing World uses: the place, the date,
the length and method, then the band one line per bell with the conductor
marked. It is not a data format, it is what a report looks like, which is
exactly why it is worth generating rather than typing.

Nothing here talks to anything over a network. This produces the text and
somebody pastes it, because a library that quietly posted a peal on somebody's
behalf would be a library nobody trusted.

Reading is here too, and is the harder half: the text is written for people, so
it is read as leniently as it can be and what cannot be read is reported rather
than guessed at.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import re
from dataclasses import dataclass
from datetime import date

from blueline.core.bands import Band, BandError
from blueline.core.performance import Performance, PerformanceError
from blueline.errors import BluelineError
from blueline.io.loading import LoadError

#: How a bell is written at the front of a band line. The tenor is often given
#: as a name rather than a number, which is why the word is allowed.
BELL = re.compile(r"^\s*(\d+|treble|tenor)\s*[.:)]?\s+(.+?)\s*$", re.IGNORECASE)

#: The conductor is marked with a trailing (c) or (conductor).
CONDUCTOR = re.compile(r"\s*\((?:c|cond|conductor)\)\s*$", re.IGNORECASE)

DATE_FORMAT = "%A, %d %B %Y"


class BellboardError(LoadError):
    """A performance report that cannot be read."""


@dataclass(frozen=True)
class Report:
    """A performance as it reads in a report."""

    lines: Tuple[str, ...]

    def __str__(self) -> str:
        return "\n".join(self.lines)


def _band_lines(performance: Performance) -> List[str]:
    band = performance.band
    out: List[str] = []
    for bell in range(1, band.stage + 1):
        name = band.on(bell)
        mark = " (C)" if bell == band.conductor else ""
        out.append(f"{bell} {name}{mark}")
    return out


def write(performance: Performance) -> Report:
    """The performance, as it would be pasted in."""
    lines = [
        performance.place.strip(),
        f"{performance.rang_on:{DATE_FORMAT}}",
        "",
        f"{performance.length} {performance.title.strip()}",
    ]
    if performance.composer:
        lines.append(f"Composed by {performance.composer.strip()}")
    lines.append("")
    lines.extend(_band_lines(performance))
    return Report(tuple(lines))


def _bell_number(word: str, stage: int) -> int:
    lowered = word.strip().lower()
    if lowered == "treble":
        return 1
    if lowered == "tenor":
        return stage
    return int(lowered)


def _length_and_title(line: str) -> Tuple[int, str]:
    words = line.strip().split(maxsplit=1)
    if len(words) != 2:
        raise BellboardError(f"{line!r} does not say a length and a method")
    try:
        length = int(words[0].replace(",", ""))
    except ValueError:
        raise BellboardError(f"{words[0]!r} is not a length") from None
    return length, words[1].strip()


def read(text: str, stage: int) -> Performance:
    """Read a report back into a performance.

    The stage has to be given rather than counted off the band, because a band
    line that failed to parse would otherwise silently turn a peal of major
    into a peal of triples.
    """
    lines = [line.strip() for line in text.splitlines()]
    filled = [line for line in lines if line]
    if len(filled) < 4:
        raise BellboardError("a report needs a place, a date, a length and a band")

    place, when, what, *rest = filled
    try:
        rang_on = _parse_date(when)
    except ValueError as error:
        raise BellboardError(f"{when!r} is not a date this can read") from error

    composer: Optional[str] = None
    if rest and rest[0].lower().startswith("composed by"):
        composer = rest[0][len("composed by"):].strip() or None
        rest = rest[1:]

    length, title = _length_and_title(what)
    band = _read_band(rest, stage)
    try:
        return Performance(
            band=band,
            title=title,
            stage=stage,
            length=length,
            rang_on=rang_on,
            place=place,
            composer=composer,
        )
    except (PerformanceError, BluelineError) as error:
        raise BellboardError(str(error)) from error


def _parse_date(text: str) -> date:
    """A date as a report writes it, or as a machine writes it."""
    from datetime import datetime

    for shape in (DATE_FORMAT, "%d %B %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text.strip(), shape).date()
        except ValueError:
            continue
    raise ValueError(text)


def _read_band(lines: List[str], stage: int) -> Band:
    names: Dict[int, str] = {}
    conductor = 0
    for line in lines:
        match = BELL.match(line)
        if match is None:
            raise BellboardError(f"{line!r} is not a band line")
        rest = match.group(2)
        if CONDUCTOR.search(rest):
            rest = CONDUCTOR.sub("", rest)
            conductor = _bell_number(match.group(1), stage)
        bell = _bell_number(match.group(1), stage)
        if bell in names:
            raise BellboardError(f"bell {bell} is given twice")
        names[bell] = rest.strip()

    missing = [bell for bell in range(1, stage + 1) if bell not in names]
    if missing:
        raise BellboardError(f"nobody is on bell {missing[0]}")

    try:
        return Band(
            ringers=tuple(names[bell] for bell in range(1, stage + 1)),
            conductor=conductor or 1,
        )
    except BandError as error:
        raise BellboardError(str(error)) from error
