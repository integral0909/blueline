"""Tables about the service itself."""

from __future__ import annotations

from blueline.cli.table import Table

from blueline.cli.render.common import fields, listing, yes_no
from blueline.config import Settings
from blueline.service.checking import CheckReport


def settings_table(settings: Settings) -> Table:
    """Where this copy is pointed."""
    return fields(
        "settings",
        [
            ("database", settings.database_url),
            ("in memory", yes_no(settings.is_in_memory) if settings.is_in_memory else None),
            ("creates tables", yes_no(settings.create_tables)),
            ("seeds on start", yes_no(settings.seed_on_start)),
            ("echoes sql", yes_no(settings.echo_sql) if settings.echo_sql else None),
            ("request limit", f"{settings.request_limit} per {int(settings.request_window)}s"),
        ],
    )


def check_table(report: CheckReport) -> Table:
    """What looking over the library turned up."""
    table = listing(
        report.summary(),
        [
            ("", {"style": "dim"}),
            ("subject", {"overflow": "ellipsis", "max_width": 30}),
            ("detail", {"overflow": "fold"}),
        ],
    )
    for finding in report.findings:
        table.add_row(finding.level, finding.subject, finding.detail)
    return table
