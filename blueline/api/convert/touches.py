"""Turning the touch service's answers into wire shapes."""

from __future__ import annotations

from typing import Any, Dict, Optional

from blueline.api.convert.common import counted_music
from blueline.core.peals import Standing
from blueline.core.rounds import RoundsAt
from blueline.service.calls import PositionView, PrintedView
from blueline.service.proving import TouchReport
from blueline.service.searching import (
    MusicReport,
    Ranked,
    SearchReport,
    TargetReport,
)
from blueline.service.spliced import SplicedReport


def standing_out(standing: Standing) -> Dict[str, Any]:
    return {
        "counts_as": standing.counts_as,
        "short_by": standing.short_by,
    }


def rounds_at_out(where: Optional[RoundsAt]) -> Optional[Dict[str, Any]]:
    if where is None:
        return None
    return {
        "row": where.row,
        "lead": where.lead,
        "at_lead_end": where.at_lead_end,
    }


def touch_out(report: TouchReport) -> Dict[str, Any]:
    return {
        "title": report.title,
        "calling": report.calling,
        "leads": report.leads,
        "length": report.length,
        "comes_round": report.comes_round,
        "is_true": report.is_true,
        "is_extent": report.is_extent,
        "extent_length": report.extent_length,
        "is_ringable": report.is_ringable,
        "summary": report.summary(),
        "final_row": report.final_row,
        "standing": standing_out(report.standing),
        "early_rounds": rounds_at_out(report.outcome.early_rounds),
        "stands_at_a_lead_end": report.outcome.stands_at_a_lead_end,
        "repeats": [
            {
                "row": str(repeat.row),
                "positions": list(repeat.positions),
            }
            for repeat in report.repeats
        ],
        "music": counted_music(report.music),
    }


def search_out(report: SearchReport) -> Dict[str, Any]:
    return {
        "title": report.title,
        "count": len(report.found),
        "exhausted": report.exhausted,
        "looked_at": report.looked_at,
        "summary": report.summary(),
        "found": [
            {
                "calling": entry.calling,
                "leads": entry.leads,
                "length": entry.length,
            }
            for entry in report.found
        ],
    }


def splice_out(report: SplicedReport) -> Dict[str, Any]:
    return {
        "order": report.order,
        "calling": report.calling,
        "methods_used": list(report.methods_used),
        "leads": report.leads,
        "length": report.length,
        "comes_round": report.comes_round,
        "is_true": report.is_true,
        "is_ringable": report.is_ringable,
        "summary": report.summary(),
        "final_row": report.final_row,
        "standing": standing_out(report.standing),
        "early_rounds": rounds_at_out(report.outcome.early_rounds),
        "stands_at_a_lead_end": report.outcome.stands_at_a_lead_end,
        "repeats": [
            {
                "row": str(repeat.row),
                "positions": list(repeat.positions),
            }
            for repeat in report.repeats
        ],
        "music": counted_music(report.music),
    }


def target_out(report: TargetReport) -> Dict[str, Any]:
    return {
        "title": report.title,
        "target": report.target,
        "wanted": report.wanted,
        "reachable": report.reachable,
        "why_not": report.why_not,
        "exhausted": report.exhausted,
        "count": len(report.found),
        "summary": report.summary(),
        "found": [
            {
                "calling": entry.calling,
                "leads": entry.leads,
                "length": entry.length,
            }
            for entry in report.found
        ],
    }


def position_out(view: PositionView) -> Dict[str, Any]:
    return {
        "name": view.name,
        "lead": view.lead,
        "tenor_place": view.tenor_place,
    }


def ranked_out(entry: Ranked) -> Dict[str, Any]:
    return {
        "calling": entry.calling,
        "leads": entry.leads,
        "length": entry.length,
        "score": entry.score,
        "per_row": entry.per_row,
        "music": entry.music,
    }


def music_search_out(report: MusicReport) -> Dict[str, Any]:
    return {
        "title": report.title,
        "considered": report.considered,
        "exhausted": report.exhausted,
        "best": [ranked_out(entry) for entry in report.best],
        "summary": report.summary(),
    }


def printed_out(view: PrintedView) -> Dict[str, Any]:
    return {
        "printed": view.printed,
        "tidied": view.tidied,
        "positions": list(view.positions),
        "parts": view.parts,
        "calling": view.calling,
        "touch": touch_out(view.touch),
        "summary": view.summary(),
    }
