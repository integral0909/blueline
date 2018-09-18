"""Turning the method service's answers into wire shapes."""

from __future__ import annotations

from typing import Any, Dict

from blueline.analysis import MethodReport
from blueline.api.convert.common import counted_music
from blueline.api.convert.compositions import composition_out
from blueline.api.convert.learning import difficulty_out
from blueline.api.convert.touches import position_out
from blueline.core.falseness import FalseCourseHead
from blueline.service.analysing import ComparisonView
from blueline.service.dossier import Dossier
from blueline.service.method_views import (
    GroupView,
    HandbellView,
    ImportReport,
    LineView,
)


def music_out(report: MethodReport) -> Dict[str, Any]:
    return counted_music(report.music)


def method_out(report: MethodReport) -> Dict[str, Any]:
    return {
        "title": str(report.title),
        "name": report.title.name,
        "stage": report.stage,
        "notation": report.notation,
        "classification": str(report.classification),
        "symmetry": report.symmetry,
        "lead_length": report.lead_length,
        "leads_in_course": report.leads_in_course,
        "course_length": report.course_length,
        "lead_head": str(report.lead_head),
        "hunt_bells": list(report.hunt_bells),
        "working_bells": list(report.working_bells),
        "coursing_order": list(report.coursing_order),
        "course_is_true": report.course_is_true,
        "music": music_out(report),
    }


def line_out(view: LineView) -> Dict[str, Any]:
    return {
        "bell": view.bell,
        "places": list(view.places),
        "described": view.described,
        "grid": list(view.grid),
        "work": dict(view.work),
    }


def false_course_head_out(entry: FalseCourseHead) -> Dict[str, Any]:
    return {
        "head": str(entry.head),
        "clashes": entry.clashes,
    }


def import_out(report: ImportReport) -> Dict[str, Any]:
    return {
        "added": list(report.added),
        "skipped": list(report.skipped),
        "problems": list(report.problems),
        "total": report.total,
        "summary": report.summary(),
    }


def handbell_pair_out(view: HandbellView) -> Dict[str, Any]:
    return {
        "pair": view.pair,
        "bells": list(view.bells),
        "crossings": list(view.crossings),
        "together": list(view.together),
        "summary": view.summary(),
    }


def lead_head_group_out(view: GroupView) -> Dict[str, Any]:
    return {
        "head": view.head,
        "order": view.order,
        "places_at_lead_end": view.places_at_lead_end,
        "titles": list(view.titles),
        "summary": view.summary(),
    }


def comparison_out(view: ComparisonView) -> Dict[str, Any]:
    return {
        "left": view.left,
        "right": view.right,
        "changes": view.changes,
        "same": view.same,
        # Rounded here so a client and the cli quote the same share.
        "share": round(view.share, 4),
        "same_lead_head": view.same_lead_head,
        "same_length": view.same_length,
        "identical": view.identical,
        "divergences": list(view.divergences),
        "work": [(bell, blows) for bell, blows in view.work],
        "summary": view.summary,
    }


def dossier_out(dossier: Dossier) -> Dict[str, Any]:
    return {
        "title": dossier.title,
        "method": method_out(dossier.report),
        "difficulty": difficulty_out(dossier.difficulty),
        "line": line_out(dossier.line),
        "place_bells": list(dossier.place_bells),
        "falseness": [false_course_head_out(each) for each in dossier.falseness],
        "handbells": [handbell_pair_out(each) for each in dossier.handbells],
        "positions": [position_out(each) for each in dossier.positions],
        "compositions": [composition_out(each) for each in dossier.compositions],
        "in_sets": list(dossier.in_sets),
        "summary": dossier.summary(),
    }
