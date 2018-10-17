"""Tables about how a band struck."""

from __future__ import annotations

from blueline.cli.table import Table

from blueline.cli.render.common import listing
from blueline.service.striking import StrikingReport


def striking_table(reports: list[StrikingReport]) -> Table:
    """A marking, in the order a judge reads it out."""
    table = listing(
        "striking" if len(reports) == 1 else f"{len(reports)} bands",
        [
            ("band", {}),
            ("faults", {"justify": "right"}),
            ("clean", {"justify": "right"}),
            ("drift", {}),
            ("worst", {"overflow": "ellipsis", "max_width": 40}),
        ],
    )
    for report in reports:
        table.add_row(
            report.band,
            str(report.faults),
            f"{report.percentage:.1f}%",
            report.drift,
            "; ".join(report.worst) or "nothing worth saying",
        )
    return table
