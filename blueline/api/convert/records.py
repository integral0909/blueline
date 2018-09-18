"""Turning the performance and tower services' answers into wire shapes."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from blueline.core.statistics import Totals, leaderboard
from blueline.service.performances import PerformanceView
from blueline.service.plans import PlanView
from blueline.service.ringers import RingerView
from blueline.service.terms import TermView
from blueline.service.towers import TowerView


def performance_out(view: PerformanceView) -> Dict[str, Any]:
    return {
        "id": view.id,
        "title": view.title,
        "stage": view.stage,
        "length": view.length,
        "rang_on": view.rang_on,
        "place": view.place,
        "composer": view.composer,
        "conductor": view.conductor,
        "ringers": list(view.ringers),
        "counts_as": view.counts_as,
        "duration_minutes": view.duration_minutes,
        "is_peal": view.is_peal,
        "has_covering_tenor": view.has_covering_tenor,
        "tower": view.tower,
        "summary": view.summary(),
        "board": list(view.board),
    }


def counts_out(pairs: List[Tuple[str, int]]) -> List[Dict[str, Any]]:
    return [{
        "name": name,
        "count": count,
    } for name, count in pairs]


def totals_out(totals: Totals, top: int = 10) -> Dict[str, Any]:
    return {
        "performances": totals.performances,
        "peals": totals.peals,
        "quarters": totals.quarters,
        "touches": totals.touches,
        "changes": totals.changes,
        "average_length": totals.average_length,
        "places": totals.places,
        "ringers": totals.ringers,
        "first": totals.first,
        "last": totals.last,
        "summary": totals.summary(),
        "top_methods": counts_out(leaderboard(totals.by_method, top=top)),
        "top_places": counts_out(leaderboard(totals.by_place, top=top)),
        "top_ringers": counts_out(leaderboard(totals.by_ringer, top=top)),
        "by_stage": dict(totals.by_stage),
    }


def tower_out(view: TowerView) -> Dict[str, Any]:
    return {
        "place": view.place,
        "bells": view.bells,
        "tenor": view.tenor,
        "tenor_pounds": view.tenor_pounds,
        "is_heavy": view.is_heavy,
        "rings_up_to": view.rings_up_to,
        "summary": view.summary(),
    }


def plan_out(view: PlanView) -> Dict[str, Any]:
    return {
        "ringers": view.ringers,
        "minutes": view.minutes,
        "used_minutes": view.used_minutes,
        "spare_minutes": view.spare_minutes,
        "changes": view.changes,
        "items": list(view.items),
        "titles": list(view.titles),
        "summary": view.summary,
        "beyond_the_band": list(view.beyond_the_band),
    }


def ringer_out(view: RingerView) -> Dict[str, Any]:
    return {
        "name": view.name,
        "can_ring": list(view.can_ring),
        "learning": list(view.learning),
        "method_count": view.method_count,
        "summary": view.summary(),
    }


def term_out(view: TermView) -> Dict[str, Any]:
    return {
        "first": view.first,
        "last": view.last,
        "night": view.night,
        "count": view.count,
        "interrupted": view.interrupted,
        "methods": list(view.methods),
        "nights": [
            {
                "when": night.when,
                "method": night.method,
                "session": night.session,
                "of": night.of,
                "note": night.note,
            }
            for night in view.nights
        ],
        "summary": view.summary(),
    }
