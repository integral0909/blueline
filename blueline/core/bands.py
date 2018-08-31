"""Who rings what, which is the other half of a performance.

A composition is only half the story. The other half is the band: eight people,
one to a bell, and which bell each of them rings is what gets written under the
composition on a peal board. A tool that produces compositions and cannot say
who rings the tenor is missing the thing that makes it a performance.

Two rules do most of the work. Nobody rings two bells, and every bell needs
somebody, so a band is a bijection onto the stage rather than a list of names.
And the conductor is one of them, which is worth holding separately because a
performance without one is not a performance.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from dataclasses import dataclass

from blueline.core.stage import bell_symbol, check_stage
from blueline.errors import BluelineError


class BandError(BluelineError):
    """A band that cannot ring the thing it has been given."""


@dataclass(frozen=True)
class Band:
    """Who rings which bell, and who is calling it."""

    ringers: Tuple[str, ...]
    conductor: int = 1

    def __post_init__(self) -> None:
        check_stage(len(self.ringers))
        cleaned = [name.strip() for name in self.ringers]
        if any(not name for name in cleaned):
            raise BandError("every bell needs somebody on it")
        lowered = [name.lower() for name in cleaned]
        if len(set(lowered)) != len(lowered):
            raise BandError("nobody can ring two bells")
        if self.conductor < 1 or self.conductor > len(self.ringers):
            raise BandError(f"there is no bell {self.conductor} for the conductor to ring")

    @property
    def stage(self) -> int:
        return len(self.ringers)

    def on(self, bell: int) -> str:
        """Who is ringing a bell."""
        if bell < 1 or bell > self.stage:
            raise BandError(f"there is no bell {bell} in a band of {self.stage}")
        return self.ringers[bell - 1].strip()

    def bell_of(self, ringer: str) -> int:
        """Which bell somebody is on."""
        wanted = ringer.strip().lower()
        for bell, name in enumerate(self.ringers, start=1):
            if name.strip().lower() == wanted:
                return bell
        raise BandError(f"{ringer} is not in this band")

    @property
    def conducted_by(self) -> str:
        return self.on(self.conductor)

    def rings(self, stage: int) -> bool:
        """Whether this band covers a stage.

        A band of eight can ring triples with the tenor covering, so a smaller
        stage is fine as long as it is only one smaller and odd.
        """
        if stage == self.stage:
            return True
        return stage == self.stage - 1 and stage % 2 == 1

    def lines(self) -> List[str]:
        """The band as it goes on a peal board, one to a line."""
        out = []
        for bell, name in enumerate(self.ringers, start=1):
            mark = " (c)" if bell == self.conductor else ""
            out.append(f"{bell_symbol(bell)} {name.strip()}{mark}")
        return out


def band_of(names: List[str], conductor: Optional[str] = None) -> Band:
    """Build a band, naming the conductor rather than counting to their bell."""
    made = Band(ringers=tuple(names))
    if conductor is None:
        return made
    return Band(ringers=made.ringers, conductor=made.bell_of(conductor))
