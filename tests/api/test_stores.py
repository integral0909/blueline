"""The repositories, as dependencies."""

from __future__ import annotations

from typing import Dict

import inspect

import pytest

from blueline.api import stores
from blueline.db.repositories import (
    CollectionRepository,
    CompetitionRepository,
    CompositionRepository,
    MethodRepository,
    PerformanceRepository,
    RingerRepository,
    TowerRepository,
)

EXPECTED = {
    "methods": MethodRepository,
    "compositions": CompositionRepository,
    "performances": PerformanceRepository,
    "towers": TowerRepository,
    "ringers": RingerRepository,
    "competitions": CompetitionRepository,
    "collections": CollectionRepository,
}


def dependencies() -> Dict[str, object]:
    """The repository builders, which is everything but session_of."""
    return {
        name: value
        for name, value in vars(stores).items()
        if inspect.isfunction(value)
        and not name.startswith("_")
        and name != "session_of"
        and value.__module__ == stores.__name__
    }


class Asking:
    """Something shaped like a request, carrying a session."""

    def __init__(self, session) -> None:
        self.state = {"session": session}


class TestDependencies:
    def test_there_is_one_per_repository(self) -> None:
        assert set(dependencies()) == set(EXPECTED)

    @pytest.mark.parametrize("name", sorted(EXPECTED))
    def test_each_gives_back_what_it_says(self, name, session) -> None:
        assert isinstance(dependencies()[name](Asking(session)), EXPECTED[name])

    @pytest.mark.parametrize("name", sorted(EXPECTED))
    def test_each_reads_the_session_off_the_request(self, name, session) -> None:
        # All of them go through session_of, so a handler cannot end up with
        # two repositories looking at different transactions.
        assert dependencies()[name](Asking(session)).session is session

    def test_they_all_use_the_session_they_are_given(self, session) -> None:
        asking = Asking(session)
        built = [make(asking) for make in dependencies().values()]
        assert all(each.session is session for each in built)


class TestNoRouterBuildsItsOwn:
    """Two routers each writing their own methods dependency is how two
    handlers in one application end up disagreeing about how one is built."""

    def test_no_router_defines_a_repository_dependency(self) -> None:
        import pkgutil

        import blueline.api.routers as package

        for module in pkgutil.iter_modules(package.__path__):
            source = package.__path__[0] + "/" + module.name + ".py"
            with open(source) as handle:
                text = handle.read()
            assert "Repository(session)" not in text, module.name


class TestThroughTheApplication:
    def test_a_listing_still_answers(self, seeded):
        assert seeded.get("/methods").status_code == 200

    def test_two_stores_on_one_request_share_a_session(self, seeded):
        # The composition endpoint takes both the compositions and the
        # methods, and storing one attaches a row built through the second to
        # a row fetched through the first.
        response = seeded.post(
            "/compositions",
            json={"title": "A 60", "method": "Plain Bob Minor", "calling": "---"},
        )
        assert response.status_code == 201
