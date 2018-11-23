"""Turning a set of methods into the shape that goes over the wire."""

from __future__ import annotations

from typing import Any, Dict

from blueline.api.convert.learning import difficulty_out
from blueline.service.collections import CollectionView, CoverageView


def collection_out(view: CollectionView) -> Dict[str, Any]:
    return {
        "name": view.name,
        "note": view.note,
        "size": view.size,
        "titles": list(view.titles),
        "not_stored": list(view.not_stored),
        "difficulties": [difficulty_out(each) for each in view.difficulties],
        "splices": view.splices,
        "why_not": view.why_not,
        "summary": view.summary(),
    }


def coverage_out(view: CoverageView) -> Dict[str, Any]:
    return {
        "name": view.name,
        "size": view.size,
        "rings": view.rings,
        # Rounded here rather than in the service, so a client and the cli
        # quote the same share.
        "share": round(view.share, 4),
        "missing": list(view.missing),
        "summary": view.summary(),
    }
