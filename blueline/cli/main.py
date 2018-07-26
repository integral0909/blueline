"""The command line.

Sits on the same service layer the api does, so the two cannot disagree about
what a method is or when a name is already taken.

The commands are grouped by subject rather than living in one module. There are
seventy five of them, and somebody looking for how a touch is proved should not
have to scroll past everything about performances to find it. They are still
all at the top level: nobody wants to type "blueline methods show" when
"blueline show" will do.

That flat namespace is the one thing this file has to protect. Two groups can
each register a command called "list" without either of them noticing, and the
second one silently wins. test_commands checks for it.
"""

from __future__ import annotations

from blueline.cli.commands import (
    callchanges,
    collections,
    competitions,
    compositions,
    learning,
    methods,
    performances,
    plans,
    ringers,
    service,
    striking,
    touches,
    towers,
    transfer,
)
from blueline.cli.commands.common import EXIT_FOR
from blueline.cli.declare import assemble

GROUPS = (
    methods.app,
    touches.app,
    performances.app,
    towers.app,
    plans.app,
    ringers.app,
    striking.app,
    competitions.app,
    callchanges.app,
    compositions.app,
    service.app,
    learning.app,
    collections.app,
    transfer.app,
)

app = assemble(list(GROUPS), help="Change ringing method analysis and composition proving.")

__all__ = ["EXIT_FOR", "app"]

if __name__ == "__main__":  # pragma: no cover
    app()
