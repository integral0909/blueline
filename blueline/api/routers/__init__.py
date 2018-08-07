"""Every router, in the order the application mounts them.

A tuple rather than a name each. Routes are matched in the order they were
registered, so the order here is not decoration: the analysis router's
/methods/{title}/line has to come after the library router's /methods/export or
export gets read as the name of a method. Keeping the order in one list means
it can be seen, and it stops app.py holding a second copy of the same list that
somebody has to remember to add to.
"""

from typing import Tuple

from blueline.api.wsgi import Router

from blueline.api.routers.analysis import router as analysis
from blueline.api.routers.callchanges import router as callchanges
from blueline.api.routers.collections import router as collections
from blueline.api.routers.competitions import router as competitions
from blueline.api.routers.compositions import router as compositions
from blueline.api.routers.learning import router as learning
from blueline.api.routers.library import router as library
from blueline.api.routers.performances import router as performances
from blueline.api.routers.plans import router as plans
from blueline.api.routers.ringers import router as ringers
from blueline.api.routers.service import router as service
from blueline.api.routers.striking import router as striking
from blueline.api.routers.touches import router as touches
from blueline.api.routers.towers import router as towers

#: Mounted in this order. Literal paths before parameterised ones, which is
#: why library comes before analysis.
ROUTERS: Tuple["Router", ...] = (
    service,
    library,
    analysis,
    touches,
    performances,
    towers,
    plans,
    ringers,
    striking,
    competitions,
    compositions,
    callchanges,
    learning,
    collections,
)
