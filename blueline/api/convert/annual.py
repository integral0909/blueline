"""Turning a tower's year into the shape that goes over the wire."""

from __future__ import annotations

from typing import Any, Dict

from blueline.service.annual import AnnualView, CompetitionLine


def competition_line_out(line: CompetitionLine) -> Dict[str, Any]:
    return {
        "name": line.name,
        "when": line.when,
        "entered": line.entered,
        "position": line.position,
        "bands": line.bands,
    }


def annual_out(view: AnnualView) -> Dict[str, Any]:
    return {
        "year": view.year,
        "place": view.place,
        "quiet": view.quiet,
        "performances": view.performances,
        "peals": view.peals,
        "quarters": view.quarters,
        "other": view.other,
        "changes": view.changes,
        "ringers": view.ringers,
        "repertoire": view.repertoire,
        "covers": round(view.covers, 4),
        "top_ringers": [(name, count) for name, count in view.top_ringers],
        "top_methods": [(name, count) for name, count in view.top_methods],
        "competitions": [competition_line_out(line) for line in view.competitions],
        "occasions_rung": list(view.occasions_rung),
        "summary": view.summary(),
    }
