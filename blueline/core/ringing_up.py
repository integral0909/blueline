"""Raising and lowering, which bookend every session in a tower.

Bells start down and finish down. Getting them up takes several minutes of
ringing that is not changes at all, and getting them down again the same, and a
band that has rung for an hour has spent ten minutes of it doing neither.

What matters to anybody recording a session is that raising and lowering are
timed separately from the ringing, and that a peal attempt has a lowering at
the end whether or not it came round. This is small, and leaving it out means
every session report is quietly wrong about how long the band was there.
"""

from __future__ import annotations

from typing import Dict

from dataclasses import dataclass
from datetime import timedelta

from blueline.errors import BluelineError

#: Roughly how long a ring takes to raise, by number of bells. Rules of thumb
#: from what bands actually take rather than anything official.
RAISE_MINUTES: Dict[int, int] = {6: 3, 8: 4, 10: 5, 12: 6}
DEFAULT_RAISE_MINUTES = 4


class SessionError(BluelineError):
    """A session that does not add up."""


@dataclass(frozen=True)
class Session:
    """A stretch of ringing, with the raising and lowering around it."""

    bells: int
    changes: int
    #: Rows a minute. Around thirty is ordinary for a tower of eight.
    peal_speed: float = 30.0
    raised: bool = True
    lowered: bool = True

    def __post_init__(self) -> None:
        if self.changes < 0:
            raise SessionError("cannot ring a negative number of changes")
        if self.peal_speed <= 0:
            raise SessionError("bells have to be rung at some speed")

    @property
    def _one_way(self) -> timedelta:
        """How long the ring takes to go up, which is how long it takes to come down."""
        return timedelta(minutes=RAISE_MINUTES.get(self.bells, DEFAULT_RAISE_MINUTES))

    @property
    def raise_time(self) -> timedelta:
        return self._one_way if self.raised else timedelta()

    @property
    def lower_time(self) -> timedelta:
        """Worked out on its own rather than from the raising.

        A band that finds the bells already up still lowers them afterwards,
        and reading the lowering off the raising made that session finish
        instantly.
        """
        return self._one_way if self.lowered else timedelta()

    @property
    def ringing_time(self) -> timedelta:
        return timedelta(minutes=self.changes / self.peal_speed)

    @property
    def total_time(self) -> timedelta:
        return self.raise_time + self.ringing_time + self.lower_time

    @property
    def overhead(self) -> timedelta:
        """Time spent on the bells but not on changes."""
        return self.raise_time + self.lower_time

    def summary(self) -> str:
        return (
            f"{self.changes} changes in {_minutes(self.ringing_time)}, "
            f"{_minutes(self.total_time)} on the bells"
        )


def _minutes(span: timedelta) -> str:
    """A span written the way a band would say it."""
    total = int(round(span.total_seconds() / 60))
    hours, minutes = divmod(total, 60)
    if not hours:
        return f"{minutes}m"
    return f"{hours}h{minutes:02d}m"


def speed_for(changes: int, span: timedelta) -> float:
    """How fast a band was going, in rows a minute."""
    minutes = span.total_seconds() / 60
    if minutes <= 0:
        raise SessionError("a performance takes some time")
    return changes / minutes


def time_for(changes: int, speed: float = 30.0) -> timedelta:
    """How long a length will take at a given speed."""
    if speed <= 0:
        raise SessionError("bells have to be rung at some speed")
    return timedelta(minutes=changes / speed)
