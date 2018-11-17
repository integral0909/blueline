"""What to learn next, and in what order.

Every tower teaches the same progression and nobody writes it down, which is
why a learner three methods in has no idea what is coming. The order is not
arbitrary: each step asks for one thing the last one did not, and the reason a
band teaches Bob Doubles before Grandsire is that Grandsire has two hunt bells
and Bob Doubles has one.

Nothing here is a rule about people. A ringer who wants to learn Bristol first
is welcome to and this will still say Cambridge is the easier one, because that
is a fact about the methods rather than an opinion about the ringer.

Difficulty is worked out from the method rather than looked up in a table. A
table would be a list of opinions about the twenty methods somebody thought of,
and this has to answer for anything anybody types in.
"""

from __future__ import annotations

from typing import List, Optional, Set, Tuple

from dataclasses import dataclass

from blueline.analysis import MethodReport
from blueline.core.method import Method

#: What each thing about a method costs a learner. These are weights, not
#: measurements: they are here to put methods in a sensible order and the
#: number itself does not mean anything on its own.
STAGE_COST = 2.0
HUNT_BELL_COST = 6.0
ASYMMETRY_COST = 12.0
DODGING_COST = 4.0
PLACE_COST = 3.0
LEAD_LENGTH_COST = 0.4

#: What a class of method is generally reckoned to cost on top of its shape.
#: Surprise is harder than Delight for a reason that is about where the places
#: fall rather than about how many there are, which the shape does not catch.
CLASS_COST = {
    "Principle": 8.0,
    "Bob": 0.0,
    "Place": 4.0,
    "Treble Bob": 6.0,
    "Delight": 10.0,
    "Surprise": 14.0,
    "Alliance": 12.0,
    "Hybrid": 16.0,
}


@dataclass(frozen=True)
class Difficulty:
    """How hard a method is, and what makes it hard."""

    title: str
    stage: int
    score: float
    reasons: Tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.title}: {self.score:.0f}"

    @property
    def band(self) -> str:
        """Roughly where a tower would put it.

        The thresholds are set against the standard methods rather than chosen
        first: Plain Bob at the small stages is what a learner rings, the
        Grandsires are what an improver rings, and Surprise is not either.
        """
        if self.score < 25:
            return "learner"
        if self.score < 45:
            return "improver"
        if self.score < 80:
            return "competent"
        return "advanced"


def _paths(method: Method) -> List[List[int]]:
    """Every bell's path through a lead, the closing row left off.

    The closing row is the opening row of the next lead. Counting it makes
    every bell look as though it did one more blow than it did.
    """
    return [list(method.path_of(bell)[:-1]) for bell in range(1, method.stage + 1)]


def _dodges_along(path: List[int]) -> int:
    dodges = 0
    index = 1
    while index < len(path) - 1:
        before, here, after = path[index - 1], path[index], path[index + 1]
        if before != here and after != here and (after - here) == -(here - before):
            dodges += 1
            # Skipped past, or a, b, a, b counts twice for one dodge.
            index += 2
            continue
        index += 1
    return dodges


def _places_along(path: List[int]) -> int:
    places = 0
    index = 1
    while index < len(path):
        if path[index] == path[index - 1]:
            places += 1
            # Skipped past the rest of a long place rather than counting each
            # pair inside it. Four blows in one position is one piece of work.
            while index < len(path) and path[index] == path[index - 1]:
                index += 1
            continue
        index += 1
    return places


def dodges_in(method: Method) -> int:
    """The most dodging any one bell does in a lead.

    The most rather than the average, because what makes a method hard is its
    worst place bell. Somebody who can ring seven of the eight leads is not
    somebody who can ring the method.
    """
    return max((_dodges_along(path) for path in _paths(method)), default=0)


def places_in(method: Method) -> int:
    """The most places any one bell makes in a lead.

    A place is two blows in the same position, which is what a ringer means by
    making a place.
    """
    return max((_places_along(path) for path in _paths(method)), default=0)


def difficulty_of(report: MethodReport, method: Method) -> Difficulty:
    """How hard a method is, worked out from what it does."""
    reasons: List[str] = []
    score = STAGE_COST * report.stage

    hunts = len(report.hunt_bells)
    if hunts != 1:
        score += HUNT_BELL_COST * abs(hunts - 1)
        reasons.append("no hunt bell" if hunts == 0 else f"{hunts} hunt bells")

    if report.symmetry == "none":
        score += ASYMMETRY_COST
        reasons.append("no symmetry to lean on")

    dodges = dodges_in(method)
    if dodges:
        score += DODGING_COST * min(dodges, 8)
        reasons.append(f"{dodges} dodges in a lead")

    places = places_in(method)
    if places:
        score += PLACE_COST * min(places, 8)
        reasons.append(f"{places} places in a lead")

    kind = report.classification.kind
    score += CLASS_COST.get(kind, 6.0)
    if CLASS_COST.get(kind, 0.0) >= 10:
        reasons.append(f"{kind} is a step up")

    score += LEAD_LENGTH_COST * report.lead_length

    return Difficulty(
        title=str(report.title),
        stage=report.stage,
        score=round(score, 1),
        reasons=tuple(reasons),
    )


def in_order(difficulties: List[Difficulty]) -> List[Difficulty]:
    """Easiest first, and at the same difficulty by stage then by name.

    Stage before name because a band moving up learns the minor version of a
    method before the major one, whatever the arithmetic says.
    """
    return sorted(difficulties, key=lambda each: (each.score, each.stage, each.title))


def next_after(
    difficulties: List[Difficulty],
    known: Set[str],
    how_many: int = 3,
) -> List[Difficulty]:
    """The easiest things somebody does not already ring.

    Not the next ones up from the hardest they know. A ringer who has learnt
    Cambridge out of order still has gaps behind it, and filling those is
    better advice than pushing on.
    """
    folded = {title.strip().lower() for title in known}
    left = [each for each in in_order(difficulties) if each.title.lower() not in folded]
    return left[:how_many]


def step_up(difficulties: List[Difficulty], known: Set[str]) -> Optional[Difficulty]:
    """The next thing harder than everything somebody already rings.

    What a ringer usually means by "what next": not a gap behind them, but the
    first thing beyond where they have got to.
    """
    folded = {title.strip().lower() for title in known}
    ordered = in_order(difficulties)
    hardest = max(
        (each.score for each in ordered if each.title.lower() in folded),
        default=0.0,
    )
    for each in ordered:
        if each.title.lower() not in folded and each.score > hardest:
            return each
    return None
