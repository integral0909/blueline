"""Real methods to test against.

Every one of these has been checked against what ringers actually ring: the
lead length, the number of leads in the plain course and the treble's line all
agree with the books. Inventing notation and asserting whatever came out would
prove nothing, and it caught four mistakes of mine while the core was going in.
"""

from __future__ import annotations

from blueline.core.method import Method

PLAIN_BOB_DOUBLES = Method.from_notation("Plain Bob", 5, "5.1.5.1.5,125")
PLAIN_BOB_MINOR = Method.from_notation("Plain Bob", 6, "x16x16x16,12")
PLAIN_BOB_MAJOR = Method.from_notation("Plain Bob", 8, "x18x18x18x18,12")
GRANDSIRE_DOUBLES = Method.from_notation("Grandsire", 5, "3.1.5.1.5.1.5.1.5.1")
CAMBRIDGE_MINOR = Method.from_notation("Cambridge Surprise", 6, "x36x14x12x36x14x56,12")
CAMBRIDGE_MAJOR = Method.from_notation("Cambridge Surprise", 8, "x38x14x1258x36x14x58x16x78,12")
DOUBLE_NORWICH = Method.from_notation("Double Norwich Court Bob", 8, "x14x36x58x18,18")

#: A lead that leaves no bell where it started, so every bell rings one line.
NO_HUNT_BELL = Method.from_notation("nothing fixed", 6, "x16x16x16x16x16")

#: Keyed by the shape of the plain course, for tests that want to sweep.
ALL_METHODS = (
    PLAIN_BOB_DOUBLES,
    PLAIN_BOB_MINOR,
    PLAIN_BOB_MAJOR,
    GRANDSIRE_DOUBLES,
    CAMBRIDGE_MINOR,
    CAMBRIDGE_MAJOR,
    DOUBLE_NORWICH,
)

#: What each method's plain course should come to, checked against the books.
COURSE_LENGTHS = {
    "Plain Bob 5": 40,
    "Plain Bob 6": 60,
    "Plain Bob 8": 112,
    "Grandsire 5": 30,
    "Cambridge Surprise 6": 120,
    "Cambridge Surprise 8": 224,
}


def method_id(method: Method) -> str:
    """A short name for a method, for pytest to label a case with."""
    return f"{method.name} {method.stage}"
