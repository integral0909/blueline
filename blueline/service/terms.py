"""Planning a term of practice nights.

A tower captain sits down twice a year and works out what the band is going to
learn between now and Christmas. What they need is the nights they have, minus
the ones nobody will come to, with something sensible put against each of them.

Sensible means: work through what the band cannot ring yet, easiest first, and
give each method more than one night, because nobody learns Cambridge on a
Tuesday. The number of nights a method gets is a function of how hard it is,
which core.learning already works out.

Nothing here is stored. A term plan is a piece of paper on the tower notice
board that gets ignored by March, and pretending otherwise would mean a table
full of plans nobody looks at.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from dataclasses import dataclass
from datetime import date

from blueline.core.calendar import DAY_NAMES, CalendarError, clashes, practice_nights
from blueline.core.learning import Difficulty
from blueline.db.repositories import CollectionRepository, MethodRepository, RingerRepository
from blueline.service.collections import resolve
from blueline.service.learning import advise_a_band, rank
from blueline.service.results import Result, invalid, not_found, succeeded

#: How many nights a method of each difficulty gets. A learner's method is one
#: night and Bristol is four, which is optimistic in both directions and about
#: right on average.
NIGHTS_FOR = {"learner": 1, "improver": 2, "competent": 3, "advanced": 4}

#: Longer than anybody plans. Two terms is a year, and a year planned in
#: advance is a year that gets rewritten in March.
MOST_NIGHTS = 60


@dataclass(frozen=True)
class Night:
    """One practice, and what is down for it."""

    when: date
    method: str
    session: int
    of: int
    note: str = ""

    @property
    def is_first(self) -> bool:
        return self.session == 1

    def __str__(self) -> str:
        if self.note:
            return f"{self.when:%d %b}: {self.note}"
        return f"{self.when:%d %b}: {self.method} ({self.session} of {self.of})"


@dataclass(frozen=True)
class TermView:
    """A term's practices, with something against each."""

    first: date
    last: date
    night: str
    nights: Tuple[Night, ...]
    methods: Tuple[str, ...]
    #: Nights something else is happening, which are left in with a note
    #: rather than dropped. A captain wants to see why there is a gap.
    interrupted: int

    @property
    def count(self) -> int:
        return len(self.nights)

    def summary(self) -> str:
        if not self.nights:
            return f"no {self.night}s between those dates"
        return (
            f"{self.count} {self.night}s, {len(self.methods)} methods, "
            f"{self.first:%d %b} to {self.last:%d %b}"
        )


def nights_for(difficulty: Difficulty) -> int:
    return NIGHTS_FOR.get(difficulty.band, 2)


def plan_term(
    methods: MethodRepository,
    ringers: RingerRepository,
    collections: CollectionRepository,
    first: date,
    last: date,
    weekday: int = 1,
    working_from: Optional[str] = None,
) -> Result[TermView]:
    """Lay a term's practice nights out.

    Working from a named set where one is given, otherwise from whatever the
    band cannot ring yet. A captain with a set in mind should not have to
    delete the suggestions first.
    """
    try:
        nights = practice_nights(first, last, weekday)
    except CalendarError as error:
        return invalid(str(error))
    if not nights:
        return succeeded(
            TermView(
                first=first,
                last=last,
                night=DAY_NAMES[weekday],
                nights=(),
                methods=(),
                interrupted=0,
            )
        )
    if len(nights) > MOST_NIGHTS:
        return invalid(f"{len(nights)} nights is more than a term")

    wanted = _wanted(methods, ringers, collections, working_from, len(nights))
    if not wanted.ok:
        return Result(failure=wanted.failure)

    busy = {
        occasion.when: occasion.name
        for year in {first.year, last.year}
        for occasion in clashes(nights, year)
    }

    laid_out: List[Night] = []
    used: List[str] = []
    queue = list(wanted.unwrap())
    index = 0
    session = 0
    for when in nights:
        if when in busy:
            laid_out.append(Night(when=when, method="", session=0, of=0, note=busy[when]))
            continue
        if index >= len(queue):
            laid_out.append(
                Night(when=when, method="", session=0, of=0, note="whatever the band fancies")
            )
            continue
        difficulty = queue[index]
        session += 1
        wants = nights_for(difficulty)
        laid_out.append(Night(when=when, method=difficulty.title, session=session, of=wants))
        if difficulty.title not in used:
            used.append(difficulty.title)
        if session >= wants:
            index += 1
            session = 0

    return succeeded(
        TermView(
            first=first,
            last=last,
            night=DAY_NAMES[weekday],
            nights=tuple(laid_out),
            methods=tuple(used),
            interrupted=len(busy),
        )
    )


def _ranked_library(methods: MethodRepository, how_many: int) -> Result[List[Difficulty]]:
    """The library in order, for a tower with no band entered."""
    ranked = rank(methods)
    if not ranked.ok:
        return ranked
    return succeeded(ranked.unwrap()[:how_many])


def _wanted(
    methods: MethodRepository,
    ringers: RingerRepository,
    collections: CollectionRepository,
    working_from: Optional[str],
    nights: int,
) -> Result[List[Difficulty]]:
    """What to work on, in the order to work on it."""
    if working_from is None:
        # One method per night at worst, so never ask for more than there are
        # nights: the advice is capped and asking wide costs nothing here.
        advised = advise_a_band(methods, ringers, how_many=min(nights, 10))
        if advised.ok:
            return advised
        # Nobody entered on the books. A tower that has not typed its band in
        # still wants a term plan, so fall back to the library in order. It is
        # worse advice and it is advice.
        return _ranked_library(methods, min(nights, 10))

    found = resolve(collections, working_from)
    if not found.ok:
        return Result(failure=found.failure)

    from blueline.analysis import analyse
    from blueline.core.learning import difficulty_of, in_order
    from blueline.db.repositories import to_method

    ranked: List[Difficulty] = []
    for title in found.unwrap().sorted:
        stored = methods.find(title)
        if stored is None:
            continue
        method = to_method(stored)
        ranked.append(difficulty_of(analyse(method, name=stored.name), method))
    if not ranked:
        return not_found(f"nothing in {working_from!r} is in the library")
    return succeeded(in_order(ranked))
