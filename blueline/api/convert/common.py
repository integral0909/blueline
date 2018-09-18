"""Conversions more than one subject needs."""

from __future__ import annotations

from typing import Any, Dict

from blueline.core.music import MusicCount
from blueline.service.checking import CheckReport, Finding


def counted_music(music: MusicCount) -> Dict[str, Any]:
    return {
        "named": dict(music.named),
        "runs_at_back": dict(music.runs_at_back),
        "runs_at_front": dict(music.runs_at_front),
    }


def finding_out(finding: Finding) -> Dict[str, Any]:
    return {
        "level": finding.level,
        "subject": finding.subject,
        "detail": finding.detail,
    }


def check_report_out(report: CheckReport) -> Dict[str, Any]:
    return {
        "checked": report.checked,
        "clean": report.clean,
        "problems": [finding_out(each) for each in report.problems],
        "notes": [finding_out(each) for each in report.notes],
        "summary": report.summary(),
    }
