"""Turning difficulty into the shape that goes over the wire."""

from __future__ import annotations

from typing import Any, Dict

from blueline.core.learning import Difficulty
from blueline.service.learning import AdviceView


def difficulty_out(difficulty: Difficulty) -> Dict[str, Any]:
    return {
        "title": difficulty.title,
        "stage": difficulty.stage,
        "score": difficulty.score,
        "band": difficulty.band,
        "reasons": list(difficulty.reasons),
    }


def advice_out(view: AdviceView) -> Dict[str, Any]:
    return {
        "ringer": view.ringer,
        "knows": view.knows,
        "fill_gaps": [difficulty_out(each) for each in view.fill_gaps],
        "step_up": None if view.step_up is None else difficulty_out(view.step_up),
        "summary": view.summary(),
    }
