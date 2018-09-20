"""The routers have to stay separate and stay mounted."""

from __future__ import annotations

from typing import Set

import pytest

from blueline.api.routers import (
    analysis_router,
    library_router,
    service_router,
    touches_router,
)
from blueline.api.routers.common import STATUS_FOR, refuse, unwrap
from blueline.service.results import Failure, Reason, not_found, succeeded

ROUTERS = {
    "service": service_router,
    "library": library_router,
    "analysis": analysis_router,
    "touches": touches_router,
}


def paths(router) -> Set[str]:
    return {route.path for route in router.routes}


class TestSplit:
    def test_every_router_has_something_in_it(self):
        for name, router in ROUTERS.items():
            assert paths(router), f"{name} is empty"

    def test_no_path_is_served_by_two_routers(self):
        seen: Set[str] = set()
        for router in ROUTERS.values():
            assert not (paths(router) & seen)
            seen |= paths(router)

    def test_health_is_on_the_service_router(self):
        assert "/health" in paths(service_router)

    def test_the_library_endpoints_are_together(self):
        assert "/methods" in paths(library_router)
        assert "/methods/import" in paths(library_router)

    def test_the_analysis_endpoints_are_together(self):
        assert "/analyse" in paths(analysis_router)
        assert "/methods/{title}/line/{bell}" in paths(analysis_router)

    def test_nothing_that_writes_is_in_the_analysis_router(self):
        writes = {"POST", "PUT", "PATCH", "DELETE"}
        for route in analysis_router.routes:
            assert not (route.methods & writes - {"POST"}) or route.path == "/analyse"

    def test_the_touch_endpoints_are_together(self):
        assert "/methods/{title}/prove" in paths(touches_router)
        assert "/methods/{title}/search" in paths(touches_router)

    def test_every_router_is_tagged(self):
        for router in ROUTERS.values():
            assert router.tags


class TestMounted:
    def test_every_route_reaches_the_application(self, client):
        served = {route.path for route in client.app.routes}
        for router in ROUTERS.values():
            assert paths(router) <= served

    def test_they_are_all_in_the_schema(self, client):
        schema = set(client.get("/openapi.json").json()["paths"])
        for router in ROUTERS.values():
            assert paths(router) <= schema


class TestCommon:
    def test_every_reason_maps_to_a_status(self):
        for reason in Reason:
            assert reason in STATUS_FOR

    def test_they_are_all_different(self):
        assert len(set(STATUS_FOR.values())) == len(STATUS_FOR)

    def test_none_of_them_are_a_success(self):
        assert all(code >= 400 for code in STATUS_FOR.values())

    def test_unwrapping_a_success_gives_the_value(self):
        assert unwrap(succeeded(7)) == 7

    def test_unwrapping_a_failure_raises_the_right_status(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as caught:
            unwrap(not_found("gone"))
        assert caught.value.status_code == 404

    def test_the_body_carries_the_reason_and_the_detail(self):
        error = refuse(Failure(Reason.INVALID, "bad notation"))
        assert error.detail == {"reason": "invalid", "detail": "bad notation"}
