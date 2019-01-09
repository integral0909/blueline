"""The routers have to stay separate and stay mounted."""

from __future__ import annotations

from typing import Set

import pytest

from blueline.api.routers import ROUTERS as MOUNTED
from blueline.api.routers.analysis import router as analysis_router
from blueline.api.routers.common import STATUS_FOR, refuse, unwrap
from blueline.api.routers.library import router as library_router
from blueline.api.routers.service import router as service_router
from blueline.api.routers.touches import router as touches_router
from blueline.service.results import Failure, Reason, not_found, succeeded

ROUTERS = {
    "service": service_router,
    "library": library_router,
    "analysis": analysis_router,
    "touches": touches_router,
}


def paths(router) -> Set[str]:
    return set(router.paths())


def paths_served() -> Set[str]:
    """Every path the application actually mounts."""
    return {path for router in MOUNTED for path in router.paths()}


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
            assert route.method not in (writes - {"POST"}) or route.path == "/analyse"

    def test_the_touch_endpoints_are_together(self):
        assert "/methods/{title}/prove" in paths(touches_router)
        assert "/methods/{title}/search" in paths(touches_router)

    def test_every_router_is_tagged(self):
        for router in ROUTERS.values():
            assert router.tag


class TestMountingOrder:
    def test_every_router_is_mounted_once(self):
        assert len({id(router) for router in MOUNTED}) == len(MOUNTED)

    def test_the_library_is_mounted_before_the_analysis(self):
        # /methods/export against /methods/{title}. This has bitten twice.
        assert MOUNTED.index(library_router) < MOUNTED.index(analysis_router)

    def test_nothing_is_mounted_twice(self):
        assert len({id(router) for router in MOUNTED}) == len(MOUNTED)


class TestMounted:
    def test_every_route_reaches_the_application(self, client):
        served = set(paths_served())
        for router in ROUTERS.values():
            assert paths(router) <= served

    def test_every_mounted_path_answers_something(self, client):
        # Not a 404 for the path itself. What comes back may well be a
        # refusal, but "nothing is served there" would mean it never got
        # mounted.
        for path in sorted(paths_served()):
            if "{" in path:
                continue
            reply = client.get(path)
            assert reply.status_code != 404 or "not served" not in reply.text


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
        from blueline.api.wsgi import HttpError

        with pytest.raises(HttpError) as caught:
            unwrap(not_found("gone"))
        assert caught.value.status == 404

    def test_the_refusal_carries_the_reason_and_the_detail(self):
        error = refuse(Failure(Reason.INVALID, "bad notation"))
        assert (error.reason, error.detail) == ("invalid", "bad notation")
