"""Planning a term of practice nights."""

from __future__ import annotations

from datetime import date

import pytest

from blueline.core.calendar import THURSDAY, TUESDAY
from blueline.core.ringers import Ringer
from blueline.db.repositories import CollectionRepository
from blueline.service.collections import keep
from blueline.service.results import Reason
from blueline.service.terms import MOST_NIGHTS, NIGHTS_FOR, plan_term

AUTUMN = (date(2023, 9, 5), date(2023, 12, 19))


@pytest.fixture()
def collections(loaded) -> CollectionRepository:
    return CollectionRepository(loaded.session)


@pytest.fixture()
def band(ringers):
    ringers.add(Ringer(name="Ann", can_ring=frozenset({"Plain Bob Doubles"}), learning=frozenset()))
    return ringers


class TestPlanning:
    def test_it_lays_out_the_nights(self, loaded, band, collections) -> None:
        view = plan_term(loaded, band, collections, *AUTUMN).unwrap()
        assert view.count > 10

    def test_every_night_is_a_tuesday(self, loaded, band, collections) -> None:
        view = plan_term(loaded, band, collections, *AUTUMN).unwrap()
        assert all(night.when.weekday() == TUESDAY for night in view.nights)

    def test_another_night_can_be_asked_for(self, loaded, band, collections) -> None:
        view = plan_term(loaded, band, collections, *AUTUMN, weekday=THURSDAY).unwrap()
        assert all(night.when.weekday() == THURSDAY for night in view.nights)
        assert view.night == "Thursday"

    def test_it_puts_something_against_each(self, loaded, band, collections) -> None:
        view = plan_term(loaded, band, collections, *AUTUMN).unwrap()
        assert all(night.method or night.note for night in view.nights)

    def test_a_method_gets_more_than_one_night(self, loaded, band, collections) -> None:
        view = plan_term(loaded, band, collections, *AUTUMN).unwrap()
        working = [night for night in view.nights if night.method]
        assert any(night.of > 1 for night in working)

    def test_the_sessions_run_in_order(self, loaded, band, collections) -> None:
        view = plan_term(loaded, band, collections, *AUTUMN).unwrap()
        for title in view.methods:
            sessions = [n.session for n in view.nights if n.method == title]
            assert sessions == list(range(1, len(sessions) + 1))

    def test_it_starts_with_something_easy(self, loaded, band, collections) -> None:
        view = plan_term(loaded, band, collections, *AUTUMN).unwrap()
        assert view.methods[0] != "Bristol Surprise Major"

    def test_it_skips_what_the_band_rings(self, loaded, band, collections) -> None:
        view = plan_term(loaded, band, collections, *AUTUMN).unwrap()
        assert "Plain Bob Doubles" not in view.methods

    def test_a_summary_counts_the_nights(self, loaded, band, collections) -> None:
        view = plan_term(loaded, band, collections, *AUTUMN).unwrap()
        assert "Tuesdays" in view.summary()


class TestInterruptions:
    def test_a_clash_is_left_in_with_a_note(self, loaded, band, collections) -> None:
        # Christmas Day 2023 is a Monday, so a Monday term runs into it.
        view = plan_term(
            loaded, band, collections, date(2023, 12, 1), date(2023, 12, 31), weekday=0
        ).unwrap()
        assert any("Christmas" in night.note for night in view.nights)

    def test_the_count_is_reported(self, loaded, band, collections) -> None:
        view = plan_term(
            loaded, band, collections, date(2023, 12, 1), date(2023, 12, 31), weekday=0
        ).unwrap()
        assert view.interrupted >= 1

    def test_an_interrupted_night_has_no_method(self, loaded, band, collections) -> None:
        view = plan_term(
            loaded, band, collections, date(2023, 12, 1), date(2023, 12, 31), weekday=0
        ).unwrap()
        for night in view.nights:
            if night.note and "Christmas" in night.note:
                assert night.method == ""

    def test_a_night_reads_as_a_line(self, loaded, band, collections) -> None:
        view = plan_term(loaded, band, collections, *AUTUMN).unwrap()
        assert ":" in str(view.nights[0])


class TestWorkingFromASet:
    def test_it_uses_the_set(self, loaded, band, collections) -> None:
        keep(collections, loaded, "Tuesday", ["Cambridge Surprise Minor"])
        view = plan_term(loaded, band, collections, *AUTUMN, working_from="Tuesday").unwrap()
        assert view.methods == ("Cambridge Surprise Minor",)

    def test_a_named_set_works_too(self, loaded, band, collections) -> None:
        view = plan_term(
            loaded, band, collections, *AUTUMN, working_from="the standard four"
        ).unwrap()
        assert view.methods

    def test_a_set_nobody_names(self, loaded, band, collections) -> None:
        result = plan_term(loaded, band, collections, *AUTUMN, working_from="the weasel four")
        assert result.failure.reason is Reason.NOT_FOUND

    def test_a_set_the_library_does_not_hold(self, loaded, band, collections) -> None:
        keep(collections, loaded, "Odd", ["Weasel Surprise Major"])
        result = plan_term(loaded, band, collections, *AUTUMN, working_from="Odd")
        assert result.failure.reason is Reason.NOT_FOUND


class TestEdges:
    def test_a_range_with_no_practice_in_it(self, loaded, band, collections) -> None:
        view = plan_term(loaded, band, collections, date(2023, 9, 6), date(2023, 9, 8)).unwrap()
        assert view.count == 0
        assert "no Tuesdays" in view.summary()

    def test_more_than_a_term(self, loaded, band, collections) -> None:
        result = plan_term(loaded, band, collections, date(2023, 1, 1), date(2025, 1, 1))
        assert result.failure.reason is Reason.INVALID

    def test_the_cap_is_about_a_year(self, loaded) -> None:
        assert 40 <= MOST_NIGHTS <= 80

    def test_a_day_that_does_not_exist(self, loaded, band, collections) -> None:
        result = plan_term(loaded, band, collections, *AUTUMN, weekday=9)
        assert result.failure.reason is Reason.INVALID

    def test_a_range_the_wrong_way_round(self, loaded, band, collections) -> None:
        result = plan_term(loaded, band, collections, date(2023, 12, 1), date(2023, 9, 1))
        assert result.failure.reason is Reason.INVALID

    def test_harder_methods_get_more_nights(self) -> None:
        assert NIGHTS_FOR["advanced"] > NIGHTS_FOR["learner"]

    def test_running_out_of_methods_leaves_a_note(self, loaded, band, collections) -> None:
        keep(collections, loaded, "One", ["Plain Bob Minor"])
        view = plan_term(loaded, band, collections, *AUTUMN, working_from="One").unwrap()
        assert any("fancies" in night.note for night in view.nights)


class TestNoBandEntered:
    """A tower that has not typed its band in still wants a plan."""

    def test_it_falls_back_to_the_library(self, loaded, ringers, collections) -> None:
        view = plan_term(loaded, ringers, collections, *AUTUMN).unwrap()
        assert view.methods

    def test_it_still_starts_with_something_easy(self, loaded, ringers, collections) -> None:
        view = plan_term(loaded, ringers, collections, *AUTUMN).unwrap()
        assert view.methods[0] == "Plain Bob Doubles"

    def test_an_empty_library_leaves_every_night_open(self, session, ringers) -> None:
        from blueline.db.repositories import CollectionRepository, MethodRepository

        empty = MethodRepository(session)
        view = plan_term(empty, ringers, CollectionRepository(session), *AUTUMN).unwrap()
        assert view.methods == ()
        assert all(night.note for night in view.nights)
