"""Everything worth saying about a method, worked out in one go.

The core modules each answer one question. This puts them together into the
report somebody actually wants: what the method is called, what family it
belongs to, how long a course runs, which bells hunt, what the coursing order
is and how much music falls out of a plain course.

It lives above core rather than in it because it depends on nearly all of core
at once. Putting a title on Method would have meant Method importing the
classifier, and the classifier already imports Method.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from dataclasses import dataclass

from blueline.core.classify import Classification, classify
from blueline.core.coursing import CoursingError, coursing_order
from blueline.core.method import Method
from blueline.core.music import MusicCount, count_music
from blueline.core.row import Row
from blueline.core.symmetry import describe_symmetry
from blueline.core.title import Title, title_for
from blueline.core.touch import plain_course
from blueline.core.truth import prove


@dataclass(frozen=True)
class MethodReport:
    """What a method is, in the terms a ringer would ask about."""

    title: Title
    classification: Classification
    symmetry: str
    stage: int
    lead_length: int
    leads_in_course: int
    course_length: int
    lead_head: Row
    hunt_bells: Tuple[int, ...]
    working_bells: Tuple[int, ...]
    coursing_order: Tuple[int, ...]
    course_is_true: bool
    music: MusicCount
    notation: str

    @property
    def is_principle(self) -> bool:
        return self.classification.kind == "Principle"

    @property
    def has_covering_tenor(self) -> bool:
        return self.stage % 2 == 1

    def headline(self) -> str:
        """One line describing the method, for a listing."""
        return (
            f"{self.title} ({self.notation}) "
            f"lead {self.lead_length}, course {self.course_length}"
        )


def analyse(method: Method, name: Optional[str] = None) -> MethodReport:
    """Work out everything about a method from its notation alone."""
    classification = classify(method)
    course = plain_course(method)
    rows = course.rows()[:-1]

    if method.hunt_bells:
        try:
            order = coursing_order(method)
        except CoursingError:
            order = ()
    else:
        # A principle has no hunt bell, so there is nothing for the rest to
        # course against and no coursing order to report.
        order = ()

    return MethodReport(
        title=title_for(name or method.name, method.stage, classification.kind),
        classification=classification,
        symmetry=describe_symmetry(list(method.changes)),
        stage=method.stage,
        lead_length=method.lead_length,
        leads_in_course=method.leads_in_course,
        course_length=method.course_length,
        lead_head=method.lead_head,
        hunt_bells=method.hunt_bells,
        working_bells=method.working_bells,
        coursing_order=order,
        course_is_true=prove(rows).is_true,
        music=count_music(rows),
        notation=method.notation,
    )


def compare(first: Method, second: Method) -> Dict[str, Tuple[object, object]]:
    """Where two methods differ, for putting side by side.

    Only the fields that actually differ come back. A comparison that listed
    everything would bury the two lines somebody cares about.
    """
    left, right = analyse(first), analyse(second)
    fields = {
        "stage": (left.stage, right.stage),
        "class": (str(left.classification), str(right.classification)),
        "symmetry": (left.symmetry, right.symmetry),
        "lead length": (left.lead_length, right.lead_length),
        "course length": (left.course_length, right.course_length),
        "lead head": (str(left.lead_head), str(right.lead_head)),
        "hunt bells": (left.hunt_bells, right.hunt_bells),
        "coursing order": (left.coursing_order, right.coursing_order),
    }
    return {key: pair for key, pair in fields.items() if pair[0] != pair[1]}
