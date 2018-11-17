"""Tables about how hard a method is."""

from __future__ import annotations

from blueline.cli.table import Table

from blueline.cli.render.common import fields, listing
from blueline.core.learning import Difficulty
from blueline.service.learning import AdviceView


def difficulty_table(difficulties: list[Difficulty]) -> Table:
    """Many methods, easiest first."""
    table = listing(
        f"{len(difficulties)} methods",
        [
            ("title", {"overflow": "ellipsis", "max_width": 30}),
            ("bells", {"justify": "right"}),
            ("score", {"justify": "right"}),
            ("band", {}),
            ("why", {"overflow": "ellipsis", "max_width": 34}),
        ],
    )
    for each in difficulties:
        table.add_row(
            each.title,
            str(each.stage),
            f"{each.score:.0f}",
            each.band,
            ", ".join(each.reasons),
        )
    return table


def difficulty_panel(difficulty: Difficulty) -> Table:
    """One method, down the page."""
    return fields(
        difficulty.title,
        [
            ("bells", str(difficulty.stage)),
            ("score", f"{difficulty.score:.0f}"),
            ("band", difficulty.band),
            *((f"  {index}", reason) for index, reason in enumerate(difficulty.reasons, 1)),
        ],
    )


def advice_table(view: AdviceView) -> Table:
    """What one ringer should do next."""
    rows = [
        ("rings", str(view.knows)),
        ("step up", None if view.step_up is None else view.step_up.title),
    ]
    rows.extend(
        (f"gap {index}", f"{each.title} ({each.band})")
        for index, each in enumerate(view.fill_gaps, 1)
    )
    return fields(view.ringer, rows)
