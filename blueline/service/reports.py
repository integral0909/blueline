"""What the three kinds of report have in common.

Proving a touch, proving a spliced touch and reporting a plain course all
produce the same four things: how long it was, whether it came round, whether
it was true and what music fell out. Each had grown its own copy, and the
summary wording had already drifted between them.

The shared part lives here. What is left on each report is the bit that is
genuinely its own: a calling for a touch, an order and a list of methods for a
splice.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from dataclasses import dataclass

from blueline.core.music import MusicCount, count_music
from blueline.core.peals import Standing, standing_of
from blueline.core.rounds import RoundsAt, comes_round_early, ends_at_a_lead_end
from blueline.core.row import Row
from blueline.core.truth import Repeat, prove

#: How many repeated rows a report lists before it stops. Somebody fixing a
#: composition wants the first few, not four hundred.
MAX_REPEATS = 10


@dataclass(frozen=True)
class Outcome:
    """What happened when a run of rows was rung through."""

    leads: int
    length: int
    comes_round: bool
    is_true: bool
    repeats: Tuple[Repeat, ...]
    music: MusicCount
    final_row: str
    standing: Standing
    #: Where rounds turned up before the end, if it did.
    early_rounds: Optional[RoundsAt]
    #: Whether the touch finishes somewhere a band could actually stand.
    stands_at_a_lead_end: bool

    @property
    def is_ringable(self) -> bool:
        """Whether anybody would put this on a peal board."""
        return self.comes_round and self.is_true

    def summarise(self, of_what: str = "") -> str:
        """One line saying how it went, with an optional what it was of."""
        tail = f" of {of_what}" if of_what else ""
        # Coming round early is reported ahead of falseness. The touch stops
        # there whatever else is wrong with it, so it is the thing to fix
        # first.
        if self.early_rounds is not None:
            return f"{self.length} changes{tail}, comes round early at {self.early_rounds}"
        if not self.comes_round:
            return f"{self.length} changes{tail}, does not come round"
        if not self.is_true:
            count = len(self.repeats)
            word = "row" if count == 1 else "rows"
            return f"{self.length} changes{tail}, false in {count} {word}"
        counts = self.standing.counts_as
        if counts != "touch":
            return f"{self.length} true changes{tail}, a {counts}"
        return f"{self.length} true changes{tail}"


def outcome_of(
    rows: List[Row],
    leads: int,
    stage: Optional[int] = None,
    lead_length: Optional[int] = None,
) -> Outcome:
    """Ring a run of rows through and say what happened.

    The last row is the closing one. Opening and closing on the same row is
    what coming round means, not a repeat, so it is left out of the proving.

    The stage is taken off the rows unless given. It only needs saying where
    the rows are empty, and they are not allowed to be. The lead length is
    worked out from the lead count for the same reason, and can be given where
    the leads are not all the same length, which a spliced touch's are not.
    """
    if not rows:
        raise ValueError("nothing to report on")
    rung = rows[:-1]
    proof = prove(rung)
    at_stage = stage if stage is not None else rows[0].stage
    per_lead = lead_length or (len(rung) // leads if leads else len(rung)) or 1
    return Outcome(
        leads=leads,
        length=len(rung),
        comes_round=rows[-1].is_rounds,
        is_true=proof.is_true,
        repeats=proof.repeats[:MAX_REPEATS],
        music=count_music(rung),
        final_row=str(rows[-1]),
        standing=standing_of(len(rung), at_stage),
        early_rounds=comes_round_early(rows, per_lead),
        stands_at_a_lead_end=ends_at_a_lead_end(rows, per_lead),
    )
