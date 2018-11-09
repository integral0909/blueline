"""Tables about stored compositions."""

from __future__ import annotations

from blueline.cli.table import Table

from blueline.cli.render.common import fields, listing, yes_no
from blueline.service.compositions import CompositionView


def composition_table(view: CompositionView) -> Table:
    """One composition, down the page."""
    return fields(
        view.summary(),
        [
            ("method", view.method),
            ("composer", view.composer or None),
            ("calling", view.calling),
            ("leads", str(view.leads)),
            ("changes", str(view.length)),
            ("true", yes_no(view.is_true)),
            ("comes round", yes_no(view.comes_round)),
            (
                "warning",
                None if view.still_true else "the method has changed since this went in",
            ),
        ],
    )


def composition_listing(views: list[CompositionView]) -> Table:
    """Many compositions, one per line."""
    table = listing(
        f"{len(views)} compositions",
        [
            ("id", {"justify": "right", "style": "dim"}),
            ("title", {"overflow": "ellipsis", "max_width": 26}),
            ("method", {"overflow": "ellipsis", "max_width": 24}),
            ("composer", {"overflow": "ellipsis", "max_width": 16}),
            ("changes", {"justify": "right"}),
            ("true", {}),
        ],
    )
    for view in views:
        table.add_row(
            str(view.id),
            view.title,
            view.method,
            view.composer,
            str(view.length),
            yes_no(view.is_true) if view.still_true else "changed",
        )
    return table
