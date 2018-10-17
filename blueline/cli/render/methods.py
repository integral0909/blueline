"""Tables about methods themselves."""

from __future__ import annotations

from blueline.cli.table import Table

from blueline.analysis import MethodReport
from blueline.cli.render.common import Field, bells, fields, listing, yes_no
from blueline.core.falseness import FalseCourseHead
from blueline.service.analysing import ComparisonView
from blueline.service.dossier import Dossier
from blueline.service.method_views import GroupView, HandbellView, LineView


def method_table(report: MethodReport) -> Table:
    """Everything about one method, down the page."""
    return fields(
        str(report.title),
        [
            ("notation", report.notation),
            ("class", str(report.classification)),
            ("symmetry", report.symmetry),
            ("stage", f"{report.stage}"),
            ("lead length", f"{report.lead_length}"),
            ("leads in course", f"{report.leads_in_course}"),
            ("course length", f"{report.course_length}"),
            ("lead head", str(report.lead_head)),
            ("hunt bells", bells(report.hunt_bells) or "none"),
            ("coursing order", bells(report.coursing_order) or "none"),
            ("course is true", yes_no(report.course_is_true)),
        ],
    )


def listing_table(reports: list[MethodReport]) -> Table:
    """Many methods, one per line."""
    table = listing(
        f"{len(reports)} methods",
        [
            ("title", {}),
            ("stage", {"justify": "right"}),
            ("class", {}),
            ("lead", {"justify": "right"}),
            ("course", {"justify": "right"}),
            ("notation", {"overflow": "ellipsis", "max_width": 40}),
        ],
    )
    for report in reports:
        table.add_row(
            str(report.title),
            str(report.stage),
            str(report.classification),
            str(report.lead_length),
            str(report.course_length),
            report.notation,
        )
    return table


def falseness_table(entries: list[FalseCourseHead]) -> Table:
    table = listing(
        "false course heads",
        [("head", {}), ("rows in common", {"justify": "right"})],
    )
    for entry in entries:
        table.add_row(str(entry.head), str(entry.clashes))
    return table


def line_panel(view: LineView, title: str) -> Table:
    """A bell's grid, with the row number down the side."""
    table = Table(title=f"{title}, bell {view.bell}", show_header=False)
    table.add_column("row", style="dim", justify="right")
    table.add_column("change")
    for number, row in enumerate(view.grid):
        table.add_row(str(number), row)
    return table


def work_line(view: LineView) -> str:
    """A bell's work in one line, counting rather than listing rows.

    Where the rows fall is no use to somebody learning. How many times they
    dodge is.
    """
    parts = [f"{len(rows)} {name}" for name, rows in view.work.items() if rows]
    return ", ".join(parts) if parts else "nothing to speak of"


def handbell_table(views: list[HandbellView]) -> Table:
    """What each pair does through a lead."""
    table = listing(
        "in hand",
        [("pair", {}), ("crossings", {"justify": "right"}), ("together", {"justify": "right"})],
    )
    for view in views:
        table.add_row(view.pair, str(len(view.crossings)), str(len(view.together)))
    return table


def group_table(views: list[GroupView]) -> Table:
    """Methods that take each other's compositions."""
    table = listing(
        f"{len(views)} lead head groups",
        [("lead head", {}), ("lead end", {}), ("methods", {"overflow": "fold"})],
    )
    for view in views:
        table.add_row(view.head, view.places_at_lead_end, ", ".join(view.titles))
    return table


def comparison_table(view: ComparisonView) -> Table:
    """Two methods, side by side."""
    rows: list[Field] = [
        ("agree on", f"{view.same} of {view.changes} changes"),
        ("share", f"{view.share:.0%}"),
        ("same lead head", yes_no(view.same_lead_head)),
        ("same lead length", None if view.same_length else "no"),
    ]
    # Only the first few divergences. A method that differs everywhere would
    # print its whole notation twice, which is not a comparison.
    rows.extend(("  differ", each) for each in view.divergences[:5])
    if len(view.divergences) > 5:
        rows.append(("", f"and {len(view.divergences) - 5} more"))
    rows.extend((f"  bell {bell}", f"{blows} blows the same") for bell, blows in view.work if blows)
    return fields(view.summary, rows)


def dossier_table(found: Dossier) -> Table:
    """Everything about one method, down the page."""
    report = found.report
    rows: list[Field] = [
        ("class", str(report.classification)),
        ("notation", report.notation),
        ("lead length", str(report.lead_length)),
        ("course length", str(report.course_length)),
        ("lead head", str(report.lead_head)),
        ("coursing order", bells(report.coursing_order) or None),
        ("course is true", yes_no(found.course_is_true)),
        ("difficulty", f"{found.difficulty.score:.0f} ({found.difficulty.band})"),
        ("place bells", bells(list(found.place_bells)) or None),
        ("bell " + str(found.line.bell), work_line(found.line)),
        ("positions", ", ".join(view.name for view in found.positions)),
        ("in hand", ", ".join(view.pair for view in found.handbells) or None),
        (
            "false course heads",
            ", ".join(str(each.head) for each in found.falseness) or "none",
        ),
        ("compositions", str(len(found.compositions)) if found.compositions else None),
        ("in sets", ", ".join(found.in_sets) or None),
    ]
    return fields(found.summary(), rows)
