"""Turning a sheet into the shape that goes over the wire."""

from __future__ import annotations

from typing import Any, Dict

from blueline.core.competitions import Entry
from blueline.service.competitions import CompetitionView, ProgressView


def entry_out(entry: Entry) -> Dict[str, Any]:
    return {
        "band": entry.band,
        "position": entry.position,
        "faults": entry.faults,
        "percentage": round(entry.percentage, 2),
        "drift": entry.drift,
        "note": entry.note,
    }


def competition_out(view: CompetitionView) -> Dict[str, Any]:
    return {
        "id": view.id,
        "name": view.name,
        "held_on": view.held_on,
        "place": view.place,
        "judge": view.judge,
        "stage": view.stage,
        "bands": view.bands,
        "winner": view.winner,
        "entries": [entry_out(entry) for entry in view.entries],
    }


def progress_out(view: ProgressView) -> Dict[str, Any]:
    return {
        "band": view.band,
        "entered": view.entered,
        "best": view.best,
        "improving": view.improving,
        "placings": [(held_on, place) for held_on, place in view.placings],
    }
