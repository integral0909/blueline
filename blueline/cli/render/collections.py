"""Tables about named sets of methods."""

from __future__ import annotations

from blueline.cli.table import Table

from blueline.cli.render.common import fields, listing, yes_no
from blueline.service.collections import CollectionView, CoverageView


def _splices(view: CollectionView) -> str:
    if view.splices is None:
        return view.why_not
    return yes_no(view.splices, f"no, {view.why_not}")


def collection_table(view: CollectionView) -> Table:
    """One set, down the page."""
    rows = [
        ("note", view.note or None),
        ("methods", str(view.size)),
        ("splices", _splices(view)),
        ("not in the library", ", ".join(view.not_stored) or None),
    ]
    rows.extend(
        (f"  {each.title}", f"{each.score:.0f} ({each.band})") for each in view.difficulties
    )
    return fields(view.summary(), rows)


def collection_listing(views: list[CollectionView]) -> Table:
    """Many sets, one per line."""
    table = listing(
        f"{len(views)} sets",
        [
            ("name", {"overflow": "ellipsis", "max_width": 26}),
            ("methods", {"justify": "right"}),
            ("held", {"justify": "right"}),
            ("splices", {}),
            ("note", {"overflow": "ellipsis", "max_width": 30}),
        ],
    )
    for view in views:
        table.add_row(
            view.name,
            str(view.size),
            str(view.size - len(view.not_stored)),
            "" if view.splices is None else yes_no(view.splices),
            view.note,
        )
    return table


def coverage_table(view: CoverageView) -> Table:
    """How much of a set somebody rings."""
    rows = [
        ("rings", f"{view.rings} of {view.size}"),
        ("share", f"{view.share:.0%}"),
    ]
    rows.extend(("  missing", title) for title in view.missing)
    return fields(view.name, rows)
