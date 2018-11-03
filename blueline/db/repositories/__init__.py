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

Re-exported with "as" rather than listed in an __all__ nobody remembered to
update. Forgetting one meant the linter deleted the import and the failure
turned up three files away.
"""

from blueline.db.repositories.competitions import (
    CompetitionRepository as CompetitionRepository,
)
from blueline.db.repositories.competitions import (
    to_competition as to_competition,
)
from blueline.db.repositories.competitions import (
    to_stored_competition as to_stored_competition,
)
from blueline.db.repositories.methods import (
    CompositionRepository as CompositionRepository,
)
from blueline.db.repositories.methods import (
    MethodRepository as MethodRepository,
)
from blueline.db.repositories.methods import (
    to_method as to_method,
)
from blueline.db.repositories.methods import (
    to_stored as to_stored,
)
from blueline.db.repositories.performances import (
    PerformanceRepository as PerformanceRepository,
)
from blueline.db.repositories.performances import (
    to_performance as to_performance,
)
from blueline.db.repositories.performances import (
    to_stored_performance as to_stored_performance,
)
from blueline.db.repositories.ringers import (
    RingerRepository as RingerRepository,
)
from blueline.db.repositories.ringers import (
    to_ringer as to_ringer,
)
from blueline.db.repositories.ringers import (
    to_stored_ringer as to_stored_ringer,
)
from blueline.db.repositories.towers import (
    TowerRepository as TowerRepository,
)
from blueline.db.repositories.towers import (
    to_stored_tower as to_stored_tower,
)
from blueline.db.repositories.towers import (
    to_tower as to_tower,
)
