"""Where the application is pointed, and how it says so.

Both the api and the command line needed to know which database to talk to,
and both were reaching into blueline.api.deps and assigning module globals to
do it. The tests were doing the same, which is how you end up with a test that
passes on its own and fails when something else ran first.

One object holds it now. Nothing assigns to a global from outside, and a test
builds a Settings pointing at memory and hands it over.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from blueline.db.session import DEFAULT_URL, MEMORY_URL

ENV_PREFIX = "BLUELINE_"


@dataclass(frozen=True)
class Settings:
    """Everything the application needs told from outside."""

    database_url: str = DEFAULT_URL
    #: Whether to create the tables on startup. Off where migrations run.
    create_tables: bool = True
    #: Load the standard methods into an empty database on startup.
    seed_on_start: bool = False
    echo_sql: bool = False

    @property
    def is_in_memory(self) -> bool:
        return ":memory:" in self.database_url


def _flag(name: str, default: bool) -> bool:
    """Read a boolean out of the environment without surprising anybody.

    Only the obvious words count. An unset variable is the default and
    something unrecognised is false rather than true, because a typo that
    silently turns a feature on is worse than one that leaves it off.
    """
    raw = os.environ.get(ENV_PREFIX + name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def from_env() -> Settings:
    """Settings as the environment describes them."""
    return Settings(
        database_url=os.environ.get(ENV_PREFIX + "DATABASE_URL", DEFAULT_URL),
        create_tables=_flag("CREATE_TABLES", True),
        seed_on_start=_flag("SEED_ON_START", False),
        echo_sql=_flag("ECHO_SQL", False),
    )


def for_testing() -> Settings:
    """Settings pointing at a database that vanishes afterwards."""
    return Settings(database_url=MEMORY_URL, create_tables=True, seed_on_start=False)
