"""A row is the order the bells are struck in, once.

Everything in ringing is built out of rows. A method is a way of getting from
one row to the next, a touch is a long string of them, and the whole business
of proving a composition is checking that no row turns up twice. So this is the
type everything else leans on and it is worth it being small, immutable and
quick to hash.

Rows multiply. If you have a row and you want to know where the bells end up
after a lead of some method, you transpose it by the method's lead head, and
that is the same operation as composing two permutations. Ringers write it the
other way round to mathematicians, so the code says `transposed_by` rather than
using an operator and nobody has to remember which side is which.
"""

from __future__ import annotations

from typing import List, Tuple

from dataclasses import dataclass
from functools import reduce
from math import gcd

from blueline.core.stage import bell_number, bell_symbol, check_stage, rounds_string


def _lcm(*numbers):
    """Lowest common multiple of any number of them.

    math.lcm did not arrive until 3.9, and it takes varargs, so this
    has to as well.
    """
    return reduce(lambda one, other: one * other // gcd(one, other), numbers, 1)


class RowError(ValueError):
    """A row that is not a permutation of the bells at its stage."""


@dataclass(frozen=True)
class Row:
    """The bells in the order they are struck, as bell numbers from one."""

    bells: Tuple[int, ...]

    def __post_init__(self) -> None:
        stage = len(self.bells)
        check_stage(stage)
        if sorted(self.bells) != list(range(1, stage + 1)):
            raise RowError(f"{self!s} is not a permutation of {stage} bells")

    @property
    def stage(self) -> int:
        return len(self.bells)

    def __str__(self) -> str:
        return "".join(bell_symbol(bell) for bell in self.bells)

    def __repr__(self) -> str:
        return f"Row({str(self)!r})"

    def __len__(self) -> int:
        return len(self.bells)

    def __getitem__(self, place: int) -> int:
        """The bell in a place, counting places from one as ringers do."""
        if place < 1 or place > self.stage:
            raise RowError(f"no place {place} at stage {self.stage}")
        return self.bells[place - 1]

    @classmethod
    def parse(cls, text: str) -> Row:
        """Read a row written out, such as 13527486."""
        cleaned = text.strip()
        if not cleaned:
            raise RowError("a row cannot be empty")
        return cls(tuple(bell_number(char) for char in cleaned))

    @classmethod
    def rounds(cls, stage: int) -> Row:
        """The bells in order, which is where every touch starts and ends."""
        return cls.parse(rounds_string(stage))

    @property
    def is_rounds(self) -> bool:
        return self.bells == tuple(range(1, self.stage + 1))

    def place_of(self, bell: int) -> int:
        """Which place a bell is ringing in, counting from one."""
        try:
            return self.bells.index(bell) + 1
        except ValueError as exc:
            raise RowError(f"bell {bell} is not in {self}") from exc

    def transposed_by(self, other: Row) -> Row:
        """Apply another row to this one, the way a lead head moves the bells.

        The bell that ends up in a given place is the one this row has in the
        place the other row names. Transposing rounds by anything gives that
        thing back, which is the check worth remembering.
        """
        if other.stage != self.stage:
            raise RowError(f"cannot transpose {self} by {other}, different stages")
        return Row(tuple(self.bells[place - 1] for place in other.bells))

    @property
    def inverse(self) -> Row:
        """The row that undoes this one."""
        places = [0] * self.stage
        for place, bell in enumerate(self.bells, start=1):
            places[bell - 1] = place
        return Row(tuple(places))

    @property
    def parity(self) -> int:
        """Nought if the row is even, one if it is odd.

        Half of all rows are odd, and a method that only ever swaps one pair of
        bells at a time alternates between the two. That is why an extent on an
        even stage has to be built out of changes rather than plain hunting.
        """
        seen = [False] * self.stage
        swaps = 0
        for start in range(self.stage):
            if seen[start]:
                continue
            length = 0
            step = start
            while not seen[step]:
                seen[step] = True
                step = self.bells[step] - 1
                length += 1
            swaps += length - 1
        return swaps % 2

    @property
    def is_even(self) -> bool:
        return self.parity == 0

    def swap(self, place: int) -> Row:
        """Swap the bells in a place and the one above, giving a new row."""
        if place < 1 or place >= self.stage:
            raise RowError(f"cannot swap at place {place} at stage {self.stage}")
        bells = list(self.bells)
        index = place - 1
        bells[index], bells[index + 1] = bells[index + 1], bells[index]
        return Row(tuple(bells))

    def cycles(self) -> List[Tuple[int, ...]]:
        """The row broken into the cycles the bells move round in.

        A lead head of one cycle takes the whole course to come back; several
        short cycles come round much sooner. That is what decides how many
        leads there are in a plain course.
        """
        seen = [False] * self.stage
        found: List[Tuple[int, ...]] = []
        for start in range(1, self.stage + 1):
            if seen[start - 1]:
                continue
            cycle: List[int] = []
            bell = start
            while not seen[bell - 1]:
                seen[bell - 1] = True
                cycle.append(bell)
                bell = self.bells[bell - 1]
            found.append(tuple(cycle))
        return found

    @property
    def order(self) -> int:
        """How many times the row has to be applied before rounds comes back."""
        return _lcm(*(len(cycle) for cycle in self.cycles()))
