"""Reading a composition the way it is printed.

Nobody publishes a calling as one symbol per lead. They publish it as what a
conductor says, abbreviated: "3H", "W H H", "2M, W, 2H", sometimes with a part
end and a repeat marker. That is what is in The Ringing World, what is on the
back of a peal card, and what somebody types in when they want a touch proving.

This turns that into the list of positions core.bobs already understands. It
does not know what a method is: expanding "3H" into Home, Home, Home is a fact
about the notation and not about the method it will be called in, and keeping
it that way means this can be tested without a method anywhere near it.

The abbreviations are the ones in common use. W M H B are Wrong, Middle, Home
and Before; I and O are In and Out, which are the same lead named two ways and
so are both read as Before; V and F turn up in Stedman and are left alone as
names rather than guessed at.
"""

from __future__ import annotations

from typing import List, Tuple

import re
from dataclasses import dataclass

from blueline.errors import BluelineError

#: What a printed letter means. Everything is stored under the full name that
#: core.bobs uses, so nothing downstream has to know an abbreviation exists.
LETTERS = {
    "W": "Wrong",
    "M": "Middle",
    "H": "Home",
    "B": "Before",
    "I": "Before",
    "O": "Before",
    "T": "Thirds",
    "V": "Fifths",
    "F": "Fourths",
}

#: A count in front of a position, or a bare position. "3H" and "H" both parse,
#: and so does "3 H" with a space in it because that is how half of them are
#: typed.
TERM = re.compile(r"^(?P<count>\d+)?\s*(?P<name>[A-Za-z]+)$")

#: What separates one term from the next. Commas, semicolons and whitespace all
#: appear in print and none of them mean anything different.
SEPARATORS = re.compile(r"[,;\s]+")

#: How a part is marked as repeating. "x3", "3 parts" and "3parts" all appear.
PARTS = re.compile(r"^(?:x\s*(?P<times>\d+)|(?P<count>\d+)\s*parts?)$", re.IGNORECASE)


class ShorthandError(BluelineError):
    """A printed calling that cannot be read."""


@dataclass(frozen=True)
class Composition:
    """A calling as printed: the positions, and how many parts."""

    positions: Tuple[str, ...]
    parts: int = 1

    def __post_init__(self) -> None:
        if self.parts < 1:
            raise ShorthandError(f"a composition cannot have {self.parts} parts")

    @property
    def calls(self) -> int:
        return len(self.positions) * self.parts

    def expanded(self) -> Tuple[str, ...]:
        """Every position in the whole composition, parts and all."""
        return tuple(self.positions) * self.parts

    def __str__(self) -> str:
        return format_shorthand(self)


def _name_for(word: str) -> str:
    """The full position name a printed word means."""
    cleaned = word.strip()
    if not cleaned:
        raise ShorthandError("a calling cannot have a blank position in it")
    if len(cleaned) == 1 and cleaned.upper() in LETTERS:
        return LETTERS[cleaned.upper()]
    # Spelled out in full, which conductors do for the ones that have no
    # letter. Capitalised so it matches what core.bobs answers with.
    return cleaned[:1].upper() + cleaned[1:].lower()


def _words(text: str) -> List[str]:
    """The terms in a printed calling.

    A bare number is joined onto whatever follows it, because "3 H" with a
    space in it is as common in print as "3H" and means the same thing. A
    number with nothing after it is left alone so the parser can complain
    about it rather than silently dropping a call.
    """
    words = [word for word in SEPARATORS.split(text) if word]
    joined: List[str] = []
    pending = ""
    for word in words:
        if word.isdigit():
            if pending:
                joined.append(pending)
            pending = word
            continue
        joined.append(pending + word if pending else word)
        pending = ""
    if pending:
        joined.append(pending)
    return joined


def parse_shorthand(text: str) -> Composition:
    """Read a calling as it is printed.

    A part marker anywhere in the string counts for the whole thing. It is
    written at the end almost always and at the start occasionally, and there
    is no sensible reading in which only part of a composition repeats.
    """
    stripped = text.strip()
    if not stripped:
        raise ShorthandError("there is nothing to read")

    parts = 1
    positions: List[str] = []
    for word in _words(stripped):
        repeat = PARTS.match(word)
        if repeat is not None:
            found = repeat.group("times") or repeat.group("count")
            parts = int(found)
            continue
        term = TERM.match(word)
        if term is None:
            raise ShorthandError(f"{word!r} is not a calling position")
        count = int(term.group("count") or 1)
        if count < 1:
            raise ShorthandError(f"{word!r} asks for no calls at all")
        positions.extend([_name_for(term.group("name"))] * count)

    if not positions:
        raise ShorthandError("that says how many parts but not what to call")
    return Composition(positions=tuple(positions), parts=parts)


def _shorten(name: str) -> str:
    """The letter for a position, or the name where there is not one."""
    for letter, full in LETTERS.items():
        if full == name and letter in {"W", "M", "H", "B"}:
            return letter
    return name


def format_shorthand(composition: Composition) -> str:
    """Write a calling out the way it would be printed.

    Runs of the same position are collapsed, because "3H" is what a conductor
    writes and "H H H" is what a program writes.
    """
    if not composition.positions:
        return ""

    written: List[str] = []
    run = 1
    for index, name in enumerate(composition.positions):
        ahead = composition.positions[index + 1] if index + 1 < len(composition.positions) else None
        if name == ahead:
            run += 1
            continue
        letter = _shorten(name)
        written.append(f"{run}{letter}" if run > 1 else letter)
        run = 1

    out = " ".join(written)
    return out if composition.parts == 1 else f"{out} x{composition.parts}"
