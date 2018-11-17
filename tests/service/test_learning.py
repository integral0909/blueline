"""Advice for a ringer, and for whoever is teaching them."""

from __future__ import annotations

import pytest

from blueline.core.ringers import Ringer
from blueline.service.learning import advise, advise_a_band, how_hard, rank
from blueline.service.results import Reason


@pytest.fixture()
def band(ringers):
    ringers.add(Ringer(name="Ann", can_ring=frozenset({"Plain Bob Doubles"}), learning=frozenset()))
    ringers.add(
        Ringer(
            name="Bob",
            can_ring=frozenset({"Plain Bob Doubles", "Plain Bob Minor"}),
            learning=frozenset(),
        )
    )
    ringers.add(Ringer(name="Cara", can_ring=frozenset(), learning=frozenset()))
    return ringers


class TestRank:
    def test_the_library_comes_back_in_order(self, loaded) -> None:
        ranked = rank(loaded).unwrap()
        assert [each.score for each in ranked] == sorted(each.score for each in ranked)

    def test_the_easiest_is_plain_bob_doubles(self, loaded) -> None:
        assert rank(loaded).unwrap()[0].title == "Plain Bob Doubles"

    def test_it_can_be_narrowed_to_a_stage(self, loaded) -> None:
        ranked = rank(loaded, stage=6).unwrap()
        assert all(each.stage == 6 for each in ranked)

    def test_an_empty_library(self, repository) -> None:
        assert rank(repository).unwrap() == []


class TestHowHard:
    def test_it_scores_a_method(self, loaded) -> None:
        assert how_hard(loaded, "Cambridge Surprise Minor").unwrap().score > 0

    def test_it_says_why(self, loaded) -> None:
        assert how_hard(loaded, "Cambridge Surprise Minor").unwrap().reasons

    def test_it_puts_it_in_a_band(self, loaded) -> None:
        assert how_hard(loaded, "Plain Bob Doubles").unwrap().band == "learner"

    def test_a_method_nobody_has_stored(self, loaded) -> None:
        assert how_hard(loaded, "Weasel Surprise Major").failure.reason is Reason.NOT_FOUND


class TestAdvise:
    def test_it_suggests_gaps(self, loaded, band) -> None:
        view = advise(loaded, band, "Ann").unwrap()
        assert view.fill_gaps

    def test_it_skips_what_they_already_ring(self, loaded, band) -> None:
        view = advise(loaded, band, "Ann").unwrap()
        assert all(each.title != "Plain Bob Doubles" for each in view.fill_gaps)

    def test_it_counts_what_they_know(self, loaded, band) -> None:
        assert advise(loaded, band, "Bob").unwrap().knows == 2

    def test_it_names_a_step_up(self, loaded, band) -> None:
        view = advise(loaded, band, "Bob").unwrap()
        assert view.step_up is not None

    def test_somebody_starting_out(self, loaded, band) -> None:
        view = advise(loaded, band, "Cara").unwrap()
        assert view.knows == 0
        assert view.fill_gaps[0].title == "Plain Bob Doubles"

    def test_a_summary_reads_as_advice(self, loaded, band) -> None:
        assert "could go on to" in advise(loaded, band, "Ann").unwrap().summary()

    def test_it_gives_as_many_as_asked(self, loaded, band) -> None:
        assert len(advise(loaded, band, "Ann", how_many=5).unwrap().fill_gaps) == 5

    def test_too_many_is_refused(self, loaded, band) -> None:
        assert advise(loaded, band, "Ann", how_many=99).failure.reason is Reason.INVALID

    def test_a_ringer_nobody_has_heard_of(self, loaded, band) -> None:
        assert advise(loaded, band, "Nobody").failure.reason is Reason.NOT_FOUND


class TestAdviseTheBand:
    def test_it_suggests_what_nobody_rings(self, loaded, band) -> None:
        found = advise_a_band(loaded, band).unwrap()
        assert all(each.title not in {"Plain Bob Doubles", "Plain Bob Minor"} for each in found)

    def test_it_is_in_order(self, loaded, band) -> None:
        found = advise_a_band(loaded, band).unwrap()
        assert [each.score for each in found] == sorted(each.score for each in found)

    def test_it_gives_as_many_as_asked(self, loaded, band) -> None:
        assert len(advise_a_band(loaded, band, how_many=5).unwrap()) == 5

    def test_nobody_on_the_books(self, loaded, ringers) -> None:
        assert advise_a_band(loaded, ringers).failure.reason is Reason.NOT_FOUND

    def test_too_many_is_refused(self, loaded, band) -> None:
        assert advise_a_band(loaded, band, how_many=0).failure.reason is Reason.INVALID
