"""Literal routes have to be registered before the ones that take a parameter.

FastAPI matches in registration order, so with /methods/{title} first the
request for /methods/export gets read as a method called export and answers a
404. It has bitten twice: once for export and once for the performance totals.
"""

from __future__ import annotations

from typing import List, Tuple

import re

import pytest

from blueline.api.routers import (
    analysis_router,
    competitions_router,
    library_router,
    performances_router,
    plans_router,
    towers_router,
)

ROUTERS = {
    "library": library_router,
    "competitions": competitions_router,
    "analysis": analysis_router,
    "performances": performances_router,
    "towers": towers_router,
    "plans": plans_router,
}

PARAMETER = re.compile(r"\{[^}]+\}")


def conflicts(router) -> List[Tuple[str, str]]:
    """Literal paths registered after a parameterised one that would swallow them."""
    found: List[Tuple[str, str]] = []
    seen: List[str] = []
    for route in router.routes:
        path = route.path
        for earlier in seen:
            if PARAMETER.search(earlier) and _would_swallow(earlier, path):
                found.append((earlier, path))
        seen.append(path)
    return found


def _would_swallow(pattern: str, literal: str) -> bool:
    """Whether a parameterised path would match a literal one."""
    if PARAMETER.search(literal):
        return False
    expected = PARAMETER.sub("[^/]+", pattern)
    return bool(re.fullmatch(expected, literal))


class TestOrder:
    @pytest.mark.parametrize("label", sorted(ROUTERS))
    def test_no_literal_route_is_hidden_behind_a_parameter(self, label):
        found = conflicts(ROUTERS[label])
        assert not found, f"{found[0][1]} is hidden behind {found[0][0]}"

    def test_the_helper_spots_a_real_conflict(self):
        assert _would_swallow("/methods/{title}", "/methods/export")

    def test_it_does_not_flag_a_different_depth(self):
        assert not _would_swallow("/methods/{title}", "/methods/a/b")

    def test_it_does_not_flag_two_parameterised_paths(self):
        assert not _would_swallow("/methods/{title}", "/methods/{other}")


class TestTheOnesThatBit:
    def test_export_is_reachable(self, seeded):
        assert seeded.get("/methods/export").status_code == 200

    def test_import_is_reachable(self, client):
        response = client.post("/methods/import", json={"body": "Plain, 6, x16x16x16,12"})
        assert response.status_code == 200

    def test_the_performance_totals_are_reachable(self, seeded):
        assert seeded.get("/performances/totals").status_code == 200

    def test_a_real_method_still_resolves(self, seeded):
        assert seeded.get("/methods/Plain Bob Minor").status_code == 200

    def test_a_real_performance_still_resolves(self, seeded):
        made = seeded.post(
            "/performances",
            json={
                "title": "Cambridge Surprise Major",
                "stage": 8,
                "length": 5024,
                "rang_on": "2023-03-18",
                "place": "St Andrew, Marchgate",
                "ringers": ["Ann", "Bob", "Cara", "Dan", "Eve", "Finn", "Gus", "Hana"],
            },
        ).json()
        assert seeded.get(f"/performances/{made['id']}").status_code == 200
