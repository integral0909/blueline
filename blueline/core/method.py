"""A method, and the rows it produces.

A method is a lead's worth of place notation and a name. Everything else falls
out of that: ring the changes from rounds and you have a lead, keep going and
the bells eventually come back to rounds, and the number of leads that takes is
the length of the plain course.

The bells split into two camps. A hunt bell is back where it started at the
lead head and so rings the same line every lead. The rest are working bells and
they move round one position each lead, which is what makes a course longer
than a lead.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from dataclasses import dataclass, field

from blueline.core.notation import Change, apply_all, format_notation, parse_notation
from blueline.core.row import Row
from blueline.core.stage import check_stage, is_odd_stage


class MethodError(ValueError):
    """A method that does not hold together."""


@dataclass(frozen=True)
class Method:
    """A named block of place notation at a stage."""

    name: str
    stage: int
    changes: Tuple[Change, ...] = field(compare=True)

    def __post_init__(self) -> None:
        check_stage(self.stage)
        if not self.changes:
            raise MethodError(f"{self.name} has no changes in it")
        for change in self.changes:
            if change.stage != self.stage:
                raise MethodError(
                    f"{self.name} is stage {self.stage} but has a stage {change.stage} change"
                )

    @classmethod
    def from_notation(cls, name: str, stage: int, notation: str) -> Method:
        """Build a method from notation as it would be written in a book."""
        return cls(name=name.strip(), stage=stage, changes=tuple(parse_notation(notation, stage)))

    @property
    def notation(self) -> str:
        return format_notation(list(self.changes))

    @property
    def lead_length(self) -> int:
        """How many rows there are in a lead, counting the lead head once."""
        return len(self.changes)

    def lead_rows(self, start: Optional[Row] = None) -> List[Row]:
        """The rows of one lead, from a starting row to its lead head."""
        first = start or Row.rounds(self.stage)
        if first.stage != self.stage:
            raise MethodError(f"{first} is not a stage {self.stage} row")
        return apply_all(list(self.changes), first)

    @property
    def lead_head(self) -> Row:
        """Where the bells stand after one lead from rounds."""
        return self.lead_rows()[-1]

    @property
    def leads_in_course(self) -> int:
        """How many leads it takes for the plain course to come round."""
        return self.lead_head.order

    def plain_course(self) -> List[Row]:
        """Every row of the plain course, rounds at the top and not repeated.

        The last lead head is left off because it is rounds again, and a course
        that ended by repeating its first row would be false against itself.
        """
        rows: List[Row] = []
        row = Row.rounds(self.stage)
        for _ in range(self.leads_in_course):
            rows.extend(self.lead_rows(row)[:-1])
            row = row.transposed_by(self.lead_head)
        return rows

    @property
    def course_length(self) -> int:
        return self.lead_length * self.leads_in_course

    @property
    def hunt_bells(self) -> Tuple[int, ...]:
        """Bells that are back where they started at the lead head."""
        head = self.lead_head
        return tuple(bell for place, bell in enumerate(head.bells, start=1) if bell == place)

    @property
    def working_bells(self) -> Tuple[int, ...]:
        hunting = set(self.hunt_bells)
        return tuple(bell for bell in range(1, self.stage + 1) if bell not in hunting)

    @property
    def has_covering_tenor(self) -> bool:
        return is_odd_stage(self.stage)

    def path_of(self, bell: int) -> Tuple[int, ...]:
        """The places a bell rings in through one lead, which is its blue line."""
        if bell < 1 or bell > self.stage:
            raise MethodError(f"{self.name} has no bell {bell}")
        return tuple(row.place_of(bell) for row in self.lead_rows())

    def is_true_course(self) -> bool:
        """Whether the plain course rings every row it touches only once."""
        rows = self.plain_course()
        return len(set(rows)) == len(rows)
