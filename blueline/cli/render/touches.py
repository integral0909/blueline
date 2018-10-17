"""Tables about touches: proving them, searching for them, splicing them."""

from __future__ import annotations

from blueline.cli.table import Table

from blueline.cli.render.common import Field, fields, listing, yes_no
from blueline.core.search import Found
from blueline.service.calls import PositionView, PrintedView
from blueline.service.proving import TouchReport
from blueline.service.searching import MusicReport, SearchReport, TargetReport
from blueline.service.spliced import SplicedReport


def _outcome_fields(report: TouchReport | SplicedReport) -> list[Field]:
    """What proving anything comes to, whether it was one method or eight."""
    return [
        ("leads", str(report.leads)),
        ("changes", str(report.length)),
        ("comes round", yes_no(report.comes_round, f"no, {report.final_row}")),
        ("true", yes_no(report.is_true, f"no, {len(report.repeats)} rows repeat")),
        ("counts as", str(report.standing)),
        (
            "comes round early",
            None if report.outcome.early_rounds is None else str(report.outcome.early_rounds),
        ),
    ]


def touch_table(report: TouchReport) -> Table:
    """What ringing a touch through turned up."""
    rows = _outcome_fields(report)
    if report.is_extent:
        rows.append(("extent", f"yes, all {report.extent_length}"))
    music = report.music.named
    if music:
        rows.append(("music", ", ".join(f"{name} x{count}" for name, count in music.items())))
    return fields(f"{report.title}  {report.calling}", rows)


def splice_table(report: SplicedReport) -> Table:
    """What a spliced touch does."""
    rows: list[Field] = [("methods", ", ".join(report.methods_used))]
    rows.extend(_outcome_fields(report))
    return fields(f"{report.order}  {report.calling}", rows)


def _callings_table(title: str, found: tuple[Found, ...]) -> Table:
    table = listing(
        title,
        [
            ("calling", {"overflow": "fold"}),
            ("leads", {"justify": "right"}),
            ("changes", {"justify": "right"}),
        ],
    )
    for entry in found:
        table.add_row(entry.calling, str(entry.leads), str(entry.length))
    return table


def search_table(report: SearchReport) -> Table:
    """The callings a search turned up."""
    return _callings_table(f"{report.title}: {report.summary()}", report.found)


def target_table(report: TargetReport) -> Table:
    """What looking for a particular length turned up."""
    if not report.reachable:
        table = Table(title=report.summary(), show_header=False, title_justify="left")
        table.add_column("why", style="dim")
        table.add_row(report.why_not or "")
        return table
    return _callings_table(f"{report.title}: {report.summary()}", report.found)


def position_table(views: list[PositionView]) -> Table:
    """The calling positions in a plain course."""
    table = listing(
        "calling positions",
        [("name", {}), ("lead", {"justify": "right"}), ("tenor in", {"justify": "right"})],
    )
    for view in views:
        table.add_row(view.name, str(view.lead), str(view.tenor_place))
    return table


def musical_table(report: MusicReport) -> Table:
    """The most musical of what a search turned up."""
    table = listing(
        report.summary(),
        [
            ("calling", {"overflow": "fold"}),
            ("changes", {"justify": "right"}),
            ("score", {"justify": "right"}),
            ("per row", {"justify": "right"}),
            ("music", {"overflow": "ellipsis", "max_width": 36}),
        ],
    )
    for entry in report.best:
        table.add_row(
            entry.calling,
            str(entry.length),
            f"{entry.score:.0f}",
            f"{entry.per_row:.3f}",
            entry.music,
        )
    return table


def printed_table(view: PrintedView) -> Table:
    """A printed composition, and what it comes to."""
    rows: list[Field] = [
        ("as printed", view.printed),
        ("read as", view.tidied),
        ("parts", str(view.parts) if view.parts > 1 else None),
        ("calls", str(view.calls)),
        ("positions", ", ".join(view.positions)),
    ]
    rows.extend(_outcome_fields(view.touch))
    return fields(view.summary(), rows)
