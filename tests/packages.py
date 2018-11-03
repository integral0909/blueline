"""What a package re-exports, for the tests that check the split held.

Several packages gather a subject each and re-export the pieces with "as",
which is what makes a name public rather than an accident of where it was
imported. There is no __all__ to read any more, so this reads the namespace
instead and skips the modules and the dunders.
"""

from __future__ import annotations

from typing import Dict, Set

from types import ModuleType


def exported(package: ModuleType) -> Set[str]:
    """Every public name a package hands out, submodules aside."""
    return {
        name
        for name, value in vars(package).items()
        if not name.startswith("_") and not isinstance(value, ModuleType)
    }


def duplicates(package: ModuleType) -> Set[str]:
    """Names re-exported from more than one submodule.

    Two submodules defining the same name means one of them silently wins,
    and which one depends on import order.
    """
    seen: Dict[str, str] = {}
    twice: Set[str] = set()
    for name, value in vars(package).items():
        if name.startswith("_") or isinstance(value, ModuleType):
            continue
        where = getattr(value, "__module__", "")
        if name in seen and seen[name] != where:
            twice.add(name)
        seen[name] = where
    return twice
