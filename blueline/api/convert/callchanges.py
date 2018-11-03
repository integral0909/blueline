"""Turning a call change touch into the shape that goes over the wire."""

from __future__ import annotations

from typing import Any, Dict

from blueline.service.callchanges import CallChangeReport
from blueline.service.callchanges import said as spoken


def callchange_out(report: CallChangeReport, style: str = "down") -> Dict[str, Any]:
    return {
        "stage": report.stage,
        "calls": report.calls,
        "start": report.start,
        "finish": report.finish,
        "came_round": report.came_round,
        "stood_still": report.stood_still,
        "named_reached": list(report.named_reached),
        "rows": [{
            "row": rung.row,
            "call": rung.call,
            "name": rung.name,
        } for rung in report.rows],
        # Said back in the style it was called in. A Devon band that posted a
        # calling up and got it back down would think it had been changed.
        "said": spoken(report, style).unwrap(),
    }
