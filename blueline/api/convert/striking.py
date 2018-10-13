"""Turning a marking into the shape that goes over the wire."""

from __future__ import annotations

from typing import Any, Dict, List

from blueline.service.striking import StrikingReport


def striking_out(report: StrikingReport) -> Dict[str, Any]:
    return {
        "band": report.band,
        "rows": report.rows,
        "blows": report.blows,
        "faults": report.faults,
        # Rounded here rather than in the service. A percentage carried to
        # fifteen places is a number nobody would quote and a client that has
        # to round it itself will round it differently to the cli.
        "percentage": round(report.percentage, 2),
        "spread": round(report.spread, 4),
        "drift": report.drift,
        "worst": list(report.worst),
    }


def order_out(stage: int, reports: List[StrikingReport]) -> Dict[str, Any]:
    return {
        "stage": stage,
        "bands": len(reports),
        "order": [striking_out(report) for report in reports],
    }
