"""Tables about striking competitions."""

from __future__ import annotations

from blueline.cli.table import Table

from blueline.cli.render.common import fields, listing
from blueline.service.competitions import CompetitionView, ProgressView


def competition_table(view: CompetitionView) -> Table:
    """One sheet, as it was read out."""
    table = listing(
        f"{view.name}, {view.held_on:%Y-%m-%d}",
        [
            ("", {"justify": "right", "style": "dim"}),
            ("band", {}),
            ("faults", {"justify": "right"}),
            ("clean", {"justify": "right"}),
            ("note", {"overflow": "ellipsis", "max_width": 30}),
        ],
    )
    for entry in view.entries:
        table.add_row(
            str(entry.position),
            entry.band,
            str(entry.faults),
            f"{entry.percentage:.1f}%" if entry.percentage else "",
            entry.note,
        )
    return table


def competition_listing(views: list[CompetitionView]) -> Table:
    """Many sheets, one per line."""
    table = listing(
        f"{len(views)} competitions",
        [
            ("id", {"justify": "right", "style": "dim"}),
            ("date", {}),
            ("name", {"overflow": "ellipsis", "max_width": 28}),
            ("place", {"overflow": "ellipsis", "max_width": 24}),
            ("bells", {"justify": "right"}),
            ("bands", {"justify": "right"}),
            ("won by", {"overflow": "ellipsis", "max_width": 20}),
        ],
    )
    for view in views:
        table.add_row(
            str(view.id),
            f"{view.held_on:%Y-%m-%d}",
            view.name,
            view.place,
            str(view.stage),
            str(view.bands),
            view.winner or "a tie",
        )
    return table


def progress_table(view: ProgressView) -> Table:
    """How a band has done over the years."""
    way = {True: "improving", False: "slipping", None: "too few to say"}[view.improving]
    return fields(
        view.band,
        [
            ("entered", str(view.entered)),
            ("best", None if view.best is None else str(view.best)),
            ("trend", way),
            *((f"{held_on:%Y-%m-%d}", str(place)) for held_on, place in view.placings),
        ],
    )
