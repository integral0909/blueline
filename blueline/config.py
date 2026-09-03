"""Where the application is pointed, and how it says so.

Both the api and the command line needed to know which database to talk to,
and both were reaching into blueline.api.deps and assigning module globals to
do it. The tests were doing the same, which is how you end up with a test that
passes on its own and fails when something else ran first.

One object holds it now. Nothing assigns to a global from outside, and a test
builds a Settings pointing at memory and hands it over.

Three places it can come from, in order of who wins: a file, then the
environment, then what is hard coded here. A file because a tower running this
on a machine in the vestry wants to write the settings down once rather than
export six variables in whatever starts it, and the environment on top because
that is how anything containerised gets told anything.
"""

from __future__ import annotations

from typing import Optional, Set

import os
import tomllib
from dataclasses import dataclass, fields, replace
from pathlib import Path

from blueline.db.session import DEFAULT_URL, MEMORY_URL

ENV_PREFIX = "BLUELINE_"

#: Where the settings file is looked for when nobody says. The working
#: directory rather than somewhere under the home directory, because a tower
#: running two of these against two databases wants them side by side.
DEFAULT_FILE = Path("blueline.toml")

#: The table the settings live under, so the file can hold other things later
#: without this having to guess which keys are its own.
TABLE = "blueline"


class ConfigError(Exception):
    """A settings file that cannot be read."""


@dataclass(frozen=True)
class Settings:
    """Everything the application needs told from outside."""

    database_url: str = DEFAULT_URL
    #: Whether to create the tables on startup. Off where migrations run.
    create_tables: bool = True
    #: Load the standard methods into an empty database on startup.
    seed_on_start: bool = False
    echo_sql: bool = False
    #: Requests one caller may make in a window, and how long the window is.
    #: Per process rather than per service, which is the honest thing to say
    #: about counting in a dictionary.
    request_limit: int = 240
    request_window: float = 60.0

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


def _number(name: str, default: int) -> int:
    """Read a whole number out of the environment.

    Anything that is not one falls back to the default rather than refusing to
    start. A typo in a limit is not worth taking the service down for, and the
    default is the safe direction to be wrong in.
    """
    raw = os.environ.get(ENV_PREFIX + name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def from_env() -> Settings:
    """Settings as the environment describes them."""
    return Settings(
        database_url=os.environ.get(ENV_PREFIX + "DATABASE_URL", DEFAULT_URL),
        create_tables=_flag("CREATE_TABLES", True),
        seed_on_start=_flag("SEED_ON_START", False),
        echo_sql=_flag("ECHO_SQL", False),
        request_limit=_number("REQUEST_LIMIT", 240),
        request_window=float(_number("REQUEST_WINDOW", 60)),
    )


def from_file(path: Optional[Path] = None) -> Settings:
    """Settings as a toml file describes them.

    A missing file is not an error. The file is optional and the defaults are
    a working configuration, so refusing to start because nobody wrote one
    would be rude. A file that exists and cannot be read is an error, because
    then somebody meant something by it.
    """
    where = path or DEFAULT_FILE
    if not where.exists():
        return Settings()

    try:
        document = tomllib.loads(where.read_text())
    except (tomllib.TOMLDecodeError, OSError) as error:
        raise ConfigError(f"{where}: {error}") from error

    table = document.get(TABLE, document)
    if not isinstance(table, dict):
        raise ConfigError(f"{where}: [{TABLE}] has to be a table")

    known = {field.name for field in fields(Settings)}
    unknown = set(table) - known
    if unknown:
        # Refused rather than ignored. A misspelled key that quietly does
        # nothing is how somebody spends an afternoon wondering why the limit
        # they set is not being applied.
        raise ConfigError(f"{where}: nothing called {sorted(unknown)[0]!r}")

    try:
        return Settings(**table)
    except TypeError as error:
        raise ConfigError(f"{where}: {error}") from error


def _named_in_environment() -> Set[str]:
    """Which settings the environment actually mentions."""
    return {
        name
        for name in (field.name for field in fields(Settings))
        if ENV_PREFIX + name.upper() in os.environ
    }


def load(path: Optional[Path] = None) -> Settings:
    """The settings, from the file and then the environment over the top.

    Only what the environment actually names overrides the file. Reading the
    environment into a whole Settings and using that would have every default
    quietly overwrite whatever the file said.
    """
    settings = from_file(path)
    named = _named_in_environment()
    if not named:
        return settings
    from_environment = from_env()
    return replace(
        settings,
        **{name: getattr(from_environment, name) for name in named},
    )


def for_testing() -> Settings:
    """Settings pointing at a database that vanishes afterwards."""
    return Settings(database_url=MEMORY_URL, create_tables=True, seed_on_start=False)
