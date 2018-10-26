"""Getting things in and out of the database.

The rest of the application should not be writing selects. It asks for a method
by title or for every sheet a band appears on, and where that comes from is
this package's business. It also means the service layer can be tested against
something that satisfies the same shape without a database anywhere near it.

Everything takes a session rather than opening one. Deciding where a
transaction begins and ends belongs to the caller, and a repository that
committed on its own would make it impossible to store a method and its
compositions together.

Split by subject rather than kept as one module. Five repositories and ten
converters had grown into five hundred lines where a change to how a tower is
stored sat in the middle of everything about performances. Callers still say
blueline.db.repositories, which re-exports all of this, so nothing moved.
"""

from blueline.db.repositories.competitions import (
    CompetitionRepository,
    to_competition,
    to_stored_competition,
)
from blueline.db.repositories.methods import (
    CompositionRepository,
    MethodRepository,
    to_method,
    to_stored,
)
from blueline.db.repositories.performances import (
    PerformanceRepository,
    to_performance,
    to_stored_performance,
)
from blueline.db.repositories.ringers import (
    RingerRepository,
    to_ringer,
    to_stored_ringer,
)
from blueline.db.repositories.towers import (
    TowerRepository,
    to_stored_tower,
    to_tower,
)

__all__ = [
    "CompetitionRepository",
    "CompositionRepository",
    "MethodRepository",
    "PerformanceRepository",
    "RingerRepository",
    "TowerRepository",
    "to_competition",
    "to_method",
    "to_performance",
    "to_ringer",
    "to_stored",
    "to_stored_competition",
    "to_stored_performance",
    "to_stored_ringer",
    "to_stored_tower",
    "to_tower",
]
