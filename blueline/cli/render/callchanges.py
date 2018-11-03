"""Tables about call change ringing."""

from __future__ import annotations

from blueline.cli.table import Table

from blueline.cli.render.common import fields, listing, yes_no
from blueline.service.callchanges import CallChangeReport


def callchange_table(report: CallChangeReport) -> Table:
    """What a calling came to."""
    reached = ", ".join(report.named_reached)
    return fields(
        report.summary(),
        [
            ("bells", str(report.stage)),
            ("calls", str(report.calls)),
            ("from", report.start),
            ("to", report.finish),
            ("comes round", yes_no(report.came_round)),
            ("stood still", str(report.stood_still) if report.stood_still else None),
            ("reached", reached or None),
        ],
    )


def callchange_rows(report: CallChangeReport) -> Table:
    """Every row the band stood on."""
    table = listing(
        report.summary(),
        [
            ("", {"justify": "right", "style": "dim"}),
            ("call", {}),
            ("row", {}),
            ("", {"style": "dim"}),
        ],
    )
    for number, rung in enumerate(report.rows):
        table.add_row(str(number), rung.call, rung.row, rung.name or "")
    return table
