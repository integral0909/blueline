"""Refusing a caller that is asking for more than its share."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from blueline.api import deps
from blueline.api.app import create_app
from blueline.api.middlewares.limiting import (
    ALWAYS_ALLOWED,
    LIMIT_HEADER,
    REMAINING_HEADER,
    RESET_HEADER,
    RETRY_HEADER,
    Counter,
    caller_of,
)
from blueline.config import Settings
from blueline.db.session import MEMORY_URL


@pytest.fixture()
def tight():
    """An application that gives up after three requests."""
    deps.reset()
    settings = Settings(database_url=MEMORY_URL, request_limit=3, request_window=60.0)
    with TestClient(create_app(settings)) as client:
        yield client
    deps.reset()


class TestCounter:
    def test_the_first_request_is_allowed(self) -> None:
        allowed, left, _ = Counter(limit=3).hit("a", now=0.0)
        assert allowed
        assert left == 2

    def test_it_runs_out(self) -> None:
        counter = Counter(limit=2)
        counter.hit("a", 0.0)
        counter.hit("a", 0.0)
        allowed, left, _ = counter.hit("a", 0.0)
        assert not allowed
        assert left == 0

    def test_callers_are_counted_apart(self) -> None:
        counter = Counter(limit=1)
        assert counter.hit("a", 0.0)[0]
        assert counter.hit("b", 0.0)[0]

    def test_the_window_turns_over(self) -> None:
        counter = Counter(limit=1, window=10.0)
        counter.hit("a", 0.0)
        assert not counter.hit("a", 5.0)[0]
        assert counter.hit("a", 11.0)[0]

    def test_it_says_when_the_window_resets(self) -> None:
        counter = Counter(limit=5, window=10.0)
        _, _, resets = counter.hit("a", 0.0)
        assert resets == pytest.approx(10.0)

    def test_old_callers_are_forgotten(self) -> None:
        counter = Counter(window=10.0)
        counter.hit("a", 0.0)
        counter.hit("b", 100.0)
        assert counter.forget(before=50.0) == 1
        assert set(counter.callers) == {"b"}

    def test_forgetting_keeps_the_ones_still_going(self) -> None:
        counter = Counter(window=10.0)
        counter.hit("a", 100.0)
        assert counter.forget(before=50.0) == 0


class TestCallerOf:
    def test_an_address_identifies_a_caller(self) -> None:
        class Fake:
            client = type("Client", (), {"host": "10.0.0.4"})()

        assert caller_of(Fake()) == "10.0.0.4"

    def test_nobody_at_all(self) -> None:
        class Fake:
            client = None

        assert caller_of(Fake()) == "unknown"


class TestOverHttp:
    def test_a_request_under_the_limit_answers(self, tight) -> None:
        assert tight.get("/methods").status_code == 200

    def test_the_headers_say_what_is_left(self, tight) -> None:
        response = tight.get("/methods")
        assert response.headers[LIMIT_HEADER] == "3"
        assert response.headers[REMAINING_HEADER] == "2"

    def test_the_remaining_count_goes_down(self, tight) -> None:
        tight.get("/methods")
        assert tight.get("/methods").headers[REMAINING_HEADER] == "1"

    def test_going_over_is_refused(self, tight) -> None:
        for _ in range(3):
            tight.get("/methods")
        response = tight.get("/methods")
        assert response.status_code == 429

    def test_a_refusal_says_why(self, tight) -> None:
        for _ in range(4):
            response = tight.get("/methods")
        assert response.json()["reason"] == "too-many-requests"

    def test_a_refusal_says_when_to_come_back(self, tight) -> None:
        for _ in range(4):
            response = tight.get("/methods")
        assert int(response.headers[RETRY_HEADER]) > 0

    def test_a_refusal_still_carries_the_reset(self, tight) -> None:
        for _ in range(4):
            response = tight.get("/methods")
        assert RESET_HEADER in response.headers

    def test_health_is_never_refused(self, tight) -> None:
        for _ in range(10):
            response = tight.get("/health")
        assert response.status_code == 200

    def test_readiness_is_never_refused(self, tight) -> None:
        for _ in range(10):
            response = tight.get("/ready")
        assert response.status_code == 200

    def test_what_is_always_allowed_is_all_probes(self) -> None:
        assert {"/health", "/ready"} == ALWAYS_ALLOWED

    def test_a_refused_request_is_still_logged(self, tight) -> None:
        from blueline.api.middlewares.logging import REQUEST_ID_HEADER

        for _ in range(4):
            response = tight.get("/methods")
        assert REQUEST_ID_HEADER in response.headers
