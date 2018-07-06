"""Real methods to test against.

Every one of these has been checked against what ringers actually ring: the
lead length, the number of leads in the plain course and the treble's line all
agree with the books. Inventing notation and asserting whatever came out would
prove nothing, and it caught six mistakes of mine while the core was going in.

The names are the bare names, not the titles. A method is called Plain and its
class is Bob, which together make Plain Bob Minor. Naming the method Plain Bob
here gave Plain Bob Bob Minor the first time a title was built from one.
"""

from __future__ import annotations

from blueline.core.method import Method

PLAIN_BOB_DOUBLES = Method.from_notation("Plain", 5, "5.1.5.1.5,125")
PLAIN_BOB_MINOR = Method.from_notation("Plain", 6, "x16x16x16,12")
PLAIN_BOB_MAJOR = Method.from_notation("Plain", 8, "x18x18x18x18,12")
GRANDSIRE_DOUBLES = Method.from_notation("Grandsire", 5, "3.1.5.1.5.1.5.1.5.1")
CAMBRIDGE_MINOR = Method.from_notation("Cambridge", 6, "x36x14x12x36x14x56,12")
CAMBRIDGE_MAJOR = Method.from_notation("Cambridge", 8, "x38x14x1258x36x14x58x16x78,12")
DOUBLE_NORWICH = Method.from_notation("Double Norwich Court", 8, "x14x36x58x18,18")

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
    "Plain 5": 40,
    "Plain 6": 60,
    "Plain 8": 112,
    "Grandsire 5": 30,
    "Cambridge 6": 120,
    "Cambridge 8": 224,
}


def method_id(method: Method) -> str:
    """A short name for a method, for pytest to label a case with."""
    return f"{method.name} {method.stage}"
