"""Fetching the thing a service was asked about."""

from __future__ import annotations

import pytest

from blueline.core.ringers import Ringer
from blueline.core.towers import Tower, weight_from_pounds
from blueline.db.repositories import TowerRepository
from blueline.service.lookups import (
    method_of,
    stored_method,
    stored_ringer,
    stored_tower,
)
from blueline.service.results import Reason


@pytest.fixture()
def towers(repository) -> TowerRepository:
    store = TowerRepository(repository.session)
    store.add(Tower(place="St Andrew, Marchgate", bells=8, tenor=weight_from_pounds(2604)))
    return store


class TestStoredMethod:
    def test_it_finds_one(self, loaded) -> None:
        assert stored_method(loaded, "Plain Bob Minor").unwrap().stage == 6

    def test_the_title_is_matched_loosely(self, loaded) -> None:
        assert stored_method(loaded, "  plain bob minor ").ok

    def test_one_that_is_not_there(self, loaded) -> None:
        result = stored_method(loaded, "Weasel Surprise Major")
        assert result.failure.reason is Reason.NOT_FOUND

    def test_the_message_names_what_was_asked_for(self, loaded) -> None:
        result = stored_method(loaded, "Weasel Surprise Major")
        assert "Weasel Surprise Major" in result.failure.detail


class TestMethodOf:
    def test_it_rebuilds_the_method(self, loaded) -> None:
        assert method_of(loaded, "Plain Bob Minor").unwrap().stage == 6

    def test_the_name_survives(self, loaded) -> None:
        assert method_of(loaded, "Plain Bob Minor").unwrap().name == "Plain"

    def test_one_that_is_not_there(self, loaded) -> None:
        assert method_of(loaded, "Weasel Major").failure.reason is Reason.NOT_FOUND

    def test_it_refuses_the_same_way_the_row_lookup_does(self, loaded) -> None:
        one = method_of(loaded, "Weasel Major").failure
        other = stored_method(loaded, "Weasel Major").failure
        assert one == other


class TestStoredRinger:
    def test_it_finds_one(self, ringers) -> None:
        ringers.add(Ringer(name="Ann", can_ring=frozenset(), learning=frozenset()))
        assert stored_ringer(ringers, "Ann").unwrap().name == "Ann"

    def test_one_that_is_not_there(self, ringers) -> None:
        assert stored_ringer(ringers, "Nobody").failure.reason is Reason.NOT_FOUND

    def test_the_message_names_them(self, ringers) -> None:
        assert "Nobody" in stored_ringer(ringers, "Nobody").failure.detail


class TestStoredTower:
    def test_it_finds_one(self, towers) -> None:
        assert stored_tower(towers, "St Andrew, Marchgate").unwrap().bells == 8

    def test_one_that_is_not_there(self, towers) -> None:
        assert stored_tower(towers, "Nowhere").failure.reason is Reason.NOT_FOUND


class TestOneSentence:
    """Two spellings of the same refusal is how a client matching on the
    message gets a different answer from two endpoints."""

    def test_every_missing_method_refuses_the_same_way(self, loaded) -> None:
        from blueline.service import analysis, calls, proving, searching

        details = {
            analysis.line(loaded, "Weasel Major", 1).failure.detail,
            calls.positions(loaded, "Weasel Major").failure.detail,
            proving.prove(loaded, "Weasel Major", "-").failure.detail,
            searching.search(loaded, "Weasel Major").failure.detail,
        }
        assert len(details) == 1
