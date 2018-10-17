"""Whether the service is actually able to do its job.

There is a difference between the process being up and the service being able
to answer. A handler that returns a fixed "ok" tells a load balancer the first
and lets it send traffic to a process whose database has gone away.

What is checked here is the smallest thing that proves the database is both
reachable and the right shape: a count off the methods table. A connection
that opens but has no schema behind it fails on that and should.
"""

from __future__ import annotations

from typing import Tuple

import time
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

#: How long a check may take before it counts as a failure. A database that
#: answers in two seconds is not healthy even though it did answer.
SLOW = 2.0

OK = "ok"
FAILING = "failing"
SLOW_STATUS = "slow"


@dataclass(frozen=True)
class Check:
    """One thing that was looked at."""

    name: str
    status: str
    detail: str = ""
    took: float = 0.0

    @property
    def passed(self) -> bool:
        return self.status != FAILING


@dataclass(frozen=True)
class Health:
    """What every check came to."""

    checks: Tuple[Check, ...]

    @property
    def ready(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def status(self) -> str:
        if not self.ready:
            return FAILING
        if any(check.status == SLOW_STATUS for check in self.checks):
            return SLOW_STATUS
        return OK

    def failing(self) -> Tuple[Check, ...]:
        return tuple(check for check in self.checks if not check.passed)


def check_database(session: Session, slow: float = SLOW) -> Check:
    """Ask the database something it can only answer if it is really there."""
    started = time.monotonic()
    try:
        session.execute(text("select count(*) from methods")).scalar_one()
    except SQLAlchemyError as error:
        # The driver's message carries the connection string on some backends,
        # so only the first line goes out. A readiness probe is public.
        first = str(error).splitlines()[0]
        return Check(name="database", status=FAILING, detail=first)
    took = time.monotonic() - started
    status = SLOW_STATUS if took >= slow else OK
    return Check(name="database", status=status, took=took)


def readiness(session: Session, slow: float = SLOW) -> Health:
    """Everything that has to be working for the service to answer."""
    return Health(checks=(check_database(session, slow=slow),))
