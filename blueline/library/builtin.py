"""A set of standard methods to work with out of the box.

Every one of these has been put through the analyser and comes out with the
lead length its class demands, a true plain course and the right treble line.
Anything that did not was left out rather than being included and quietly
wrong, which is why there is no Treble Bob method here yet.

The notation is the real notation and the names are the bare names, so the
titles build correctly: the method is called Cambridge, its class is Surprise
and the title is Cambridge Surprise Major.
"""

from __future__ import annotations

from typing import List, Tuple

from blueline.core.method import Method

#: name, stage, place notation
STANDARD: Tuple[Tuple[str, int, str], ...] = (
    ("Plain", 5, "5.1.5.1.5,125"),
    ("Plain", 6, "x16x16x16,12"),
    ("Plain", 7, "3.1.7.1.7.1.7,127"),
    ("Plain", 8, "x18x18x18x18,12"),
    ("Grandsire", 5, "3.1.5.1.5.1.5.1.5.1"),
    ("Grandsire", 7, "3.1.7.1.7.1.7.1.7.1.7.1.7.1"),
    ("Grandsire", 9, "3.1.9.1.9.1.9.1.9.1.9.1.9.1.9.1.9.1"),
    ("Cambridge", 6, "x36x14x12x36x14x56,12"),
    ("Cambridge", 8, "x38x14x1258x36x14x58x16x78,12"),
    ("London", 6, "36x36.14x12x36.14x14.36,12"),
    ("Yorkshire", 8, "x38x14x58x16x12x38x14x78,12"),
    ("Superlative", 8, "x36x14x58x36x14x58x36x78,12"),
    ("Lincolnshire", 8, "x38x14x58x16x14x58x36x78,12"),
    ("Rutland", 8, "x38x14x58x16x14x58x16x78,12"),
    ("Bristol", 8, "x58x14.58x58.36.14x14.58x14x18,18"),
    ("Double Norwich Court", 8, "x14x36x58x18,18"),
)


def standard_methods() -> List[Method]:
    """Build the standard set fresh, so nobody can scribble on a shared one."""
    return [Method.from_notation(name, stage, notation) for name, stage, notation in STANDARD]
