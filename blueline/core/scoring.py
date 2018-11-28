"""Ranking touches by how much of them is worth hearing.

Finding callings that come round and are true is only half of what a composer
does. Plenty of them are true and dull. What separates a composition worth
ringing from one that merely works is the music: how often rounds-like rows
turn up, how many runs come off the back, whether the tenors stay together.

A weight per kind of row, added up. The weights are somebody's opinion and are
here to be argued with, which is why they are named constants and not numbers
scattered through the arithmetic. A band that only cares about 5678s can change
one line.

Scores are per row rather than per touch, so a long touch does not beat a short
one for being long. Ranking a 1440 above a 720 because it had twice as many
runs in it would be ranking by length with extra steps.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from dataclasses import dataclass

from blueline.core.music import MusicCount, count_music
from blueline.core.row import Row

#: What a named row is worth. Rounds turning up in the middle is not music, it
#: is the touch coming round early, so it counts for nothing here and the
#: proving catches it.
NAMED_WORTH = {
    "queens": 12.0,
    "kings": 10.0,
    "tittums": 12.0,
    "backrounds": 8.0,
    "rounds": 0.0,
}
#: Anything named that this has no opinion about.
OTHER_NAMED = 6.0

#: A run off the back is worth more than the same run at the front, because it
#: is what a listener hears. Four is the shortest anybody counts.
BACK_RUN_WORTH = {4: 1.0, 5: 2.5, 6: 5.0, 7: 9.0, 8: 14.0}
FRONT_RUN_WORTH = {4: 0.5, 5: 1.2, 6: 2.5, 7: 4.5, 8: 7.0}


@dataclass(frozen=True)
class Score:
    """How musical a run of rows is."""

    rows: int
    named: float
    back: float
    front: float

    @property
    def total(self) -> float:
        return self.named + self.back + self.front

    @property
    def per_row(self) -> float:
        """What ranks touches, so length is not an advantage on its own."""
        return self.total / self.rows if self.rows else 0.0

    def __str__(self) -> str:
        return f"{self.total:.0f} over {self.rows} rows"

    def summary(self) -> str:
        parts = []
        if self.named:
            parts.append(f"{self.named:.0f} from named rows")
        if self.back:
            parts.append(f"{self.back:.0f} off the back")
        if self.front:
            parts.append(f"{self.front:.0f} at the front")
        return ", ".join(parts) or "nothing much"


def _run_worth(counts: Dict[int, int], worth: Dict[int, float]) -> float:
    total = 0.0
    for run, count in counts.items():
        # A run longer than anything weighted is worth at least as much as the
        # longest that is, rather than nothing. A ten bell method has runs this
        # table has never heard of.
        each = worth.get(run, max(worth.values()) if worth else 0.0)
        total += each * count
    return total


def score_music(music: MusicCount, rows: int) -> Score:
    """What a counted run of music comes to."""
    named = sum(NAMED_WORTH.get(name, OTHER_NAMED) * count for name, count in music.named.items())
    return Score(
        rows=rows,
        named=named,
        back=_run_worth(dict(music.runs_at_back), BACK_RUN_WORTH),
        front=_run_worth(dict(music.runs_at_front), FRONT_RUN_WORTH),
    )


def score_rows(rows: List[Row], min_run: int = 4) -> Score:
    """Count the music in some rows and say what it comes to."""
    return score_music(count_music(rows, min_run=min_run), len(rows))


def best_of(scored: List[Tuple[str, Score]], how_many: int = 10) -> List[Tuple[str, Score]]:
    """The most musical, per row, best first.

    Ties break on the total and then on the calling, so two touches that score
    the same per row come out with the longer one first and the order does not
    depend on what happened to be found first.
    """
    return sorted(
        scored,
        key=lambda pair: (-pair[1].per_row, -pair[1].total, pair[0]),
    )[:how_many]
