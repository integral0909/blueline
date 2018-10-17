"""Tables about what a band has actually rung, and where."""

from __future__ import annotations

from blueline.cli.table import Table

from blueline.cli.render.common import Field, fields, listing
from blueline.core.statistics import Totals
from blueline.service.annual import AnnualView
from blueline.service.performances import PerformanceView
from blueline.service.plans import PlanView
from blueline.service.ringers import RingerView
from blueline.service.terms import TermView
from blueline.service.towers import TowerView


def board_lines(view: PerformanceView) -> str:
    """A performance as it goes on a peal board."""
    return "\n".join(view.board)


def performance_table(views: list[PerformanceView]) -> Table:
    """Many performances, one per line."""
    table = listing(
        f"{len(views)} performances",
        [
            ("id", {"justify": "right", "style": "dim"}),
            ("date", {}),
            ("place", {"overflow": "ellipsis", "max_width": 24}),
            ("length", {"justify": "right"}),
            ("method", {"overflow": "ellipsis", "max_width": 22}),
            ("took", {"justify": "right"}),
            ("counts as", {}),
        ],
    )
    for view in views:
        table.add_row(
            str(view.id),
            f"{view.rang_on:%Y-%m-%d}",
            view.place,
            str(view.length),
            view.title,
            f"{view.duration_minutes}m",
            view.counts_as,
        )
    return table


def totals_table(totals: Totals) -> Table:
    """What a run of performances adds up to."""
    between = (
        f"{totals.first:%Y-%m-%d} and {totals.last:%Y-%m-%d}"
        if totals.first and totals.last
        else None
    )
    return fields(
        totals.summary(),
        [
            ("performances", str(totals.performances)),
            ("peals", str(totals.peals)),
            ("quarters", str(totals.quarters)),
            ("other touches", str(totals.touches)),
            ("changes", str(totals.changes)),
            ("average length", str(totals.average_length)),
            ("towers", str(totals.places)),
            ("ringers", str(totals.ringers)),
            ("between", between),
        ],
    )


def leaderboard_table(title: str, pairs: list[tuple[str, int]]) -> Table:
    """A leaderboard, most first."""
    table = listing(
        title,
        [("name", {"overflow": "ellipsis", "max_width": 34}), ("count", {"justify": "right"})],
    )
    for name, count in pairs:
        table.add_row(name, str(count))
    return table


def tower_table(views: list[TowerView]) -> Table:
    """The rings of bells, heaviest first."""
    table = listing(
        f"{len(views)} towers",
        [
            ("place", {"overflow": "ellipsis", "max_width": 32}),
            ("bells", {"justify": "right"}),
            ("tenor", {"justify": "right"}),
        ],
    )
    for view in views:
        table.add_row(view.place, str(view.bells), view.tenor)
    return table


def ringer_table(views: list[RingerView]) -> Table:
    """Everybody, and what they can ring."""
    table = listing(
        f"{len(views)} ringers",
        [
            ("name", {}),
            ("methods", {"justify": "right"}),
            ("learning", {"overflow": "ellipsis", "max_width": 34}),
        ],
    )
    for view in views:
        table.add_row(view.name, str(view.method_count), ", ".join(view.learning))
    return table


def plan_table(view: PlanView) -> Table:
    """An evening's ringing."""
    table = listing(f"{view.ringers} ringers: {view.summary}", [("ring", {})])
    for item in view.items:
        table.add_row(item)
    if view.beyond_the_band:
        table.add_section()
        table.add_row(f"beyond the band: {len(view.beyond_the_band)} methods", style="dim")
    return table


def term_table(view: TermView) -> Table:
    """A term's practice nights."""
    table = listing(
        view.summary(),
        [
            ("date", {}),
            ("ring", {"overflow": "ellipsis", "max_width": 30}),
            ("night", {"justify": "right"}),
        ],
    )
    for night in view.nights:
        table.add_row(
            f"{night.when:%d %b}",
            night.method or night.note,
            f"{night.session} of {night.of}" if night.method else "",
        )
    return table


def annual_table(view: AnnualView) -> Table:
    """A tower's year, down the page."""
    rows: list[Field] = [
        ("performances", str(view.performances)),
        ("peals", str(view.peals)),
        ("quarters", str(view.quarters)),
        ("other touches", str(view.other)),
        ("changes", str(view.changes)),
        ("methods rung", str(view.repertoire)),
        ("ringers", str(view.ringers)),
        ("band covers", f"{view.covers:.0%}"),
        ("occasions", ", ".join(view.occasions_rung) or None),
    ]
    rows.extend((f"  {name}", str(count)) for name, count in view.top_ringers)
    rows.extend((f"  {name}", str(count)) for name, count in view.top_methods)
    rows.extend(("  competition", str(line)) for line in view.competitions)
    return fields(view.summary(), rows)
