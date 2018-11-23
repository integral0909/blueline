"""What gets stored, and how.

A library held in memory is fine for the standard set, which never changes.
Anything a user adds has to outlive the process, and once compositions come
into it there is a real relationship to model: a composition is of a method,
and deleting a method out from under one would leave nonsense behind.

Methods are stored by their place notation and name rather than by everything
the analyser works out from them. The derived facts are cheap to recompute and
expensive to keep honest, and a stored classification that disagreed with the
classifier would be worse than no stored classification at all.

Split by subject rather than kept as one module, the same way the repositories
are and for the same reason: a change to how a tower is stored had ended up in
the middle of everything about performances. The base is on its own so a table
can import it without importing every other table.
"""

from blueline.db.models.base import Base as Base
from blueline.db.models.base import now as now
from blueline.db.models.collections import StoredCollection as StoredCollection
from blueline.db.models.competitions import StoredCompetition as StoredCompetition
from blueline.db.models.competitions import StoredEntry as StoredEntry
from blueline.db.models.methods import StoredComposition as StoredComposition
from blueline.db.models.methods import StoredMethod as StoredMethod
from blueline.db.models.ringers import StoredRinger as StoredRinger
from blueline.db.models.towers import StoredPerformance as StoredPerformance
from blueline.db.models.towers import StoredTower as StoredTower
