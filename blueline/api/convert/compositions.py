"""Turning a stored composition into the shape that goes over the wire."""

from __future__ import annotations

from typing import Any, Dict

from blueline.service.compositions import CompositionView


def composition_out(view: CompositionView) -> Dict[str, Any]:
    return {
        "id": view.id,
        "title": view.title,
        "method": view.method,
        "composer": view.composer,
        "calling": view.calling,
        "length": view.length,
        "leads": view.leads,
        "is_true": view.is_true,
        "comes_round": view.comes_round,
        "still_true": view.still_true,
    }
