from datetime import date

import pytest

from blueline.core.bands import band_of
from blueline.core.performance import Performance, PerformanceError
from blueline.errors import BluelineError

EIGHT = band_of(["Ann", "Bob", "Cara", "Dan", "Eve", "Finn", "Gus", "Hana"], conductor="Hana")
WHEN = date(2023, 3, 18)


def a_performance(**over) -> Performance:
    fields = {
        "band": EIGHT,
        "title": "Cambridge Surprise Major",
        "stage": 8,
        "length": 5024,
        "rang_on": WHEN,
        "place": "St Andrew, Marchgate",
        "composer": "F Ahman",
    }
    fields.update(over)
    return Performance(**fields)


class TestBuilding:
    def test_a_performance_holds_together(self):
        assert a_performance().length == 5024

    def test_it_has_to_say_what_was_rung(self):
        with pytest.raises(PerformanceError, match="what was rung"):
            a_performance(title="   ")

    def test_it_has_to_say_where(self):
        with pytest.raises(PerformanceError, match="where"):
            a_performance(place="  ")

    def test_a_length_of_nothing_is_refused(self):
        with pytest.raises(PerformanceError, match="cannot ring"):
            a_performance(length=0)

    def test_a_band_too_small_for_the_stage_is_refused(self):
        with pytest.raises(PerformanceError, match="cannot ring"):
            a_performance(stage=12)

    def test_a_band_of_eight_can_ring_triples(self):
        assert a_performance(stage=7, length=5040).stage == 7

    def test_a_band_of_eight_cannot_ring_minor(self):
        with pytest.raises(PerformanceError):
            a_performance(stage=6)

    def test_a_composer_may_be_left_off(self):
        assert a_performance(composer=None).composer is None

    def test_a_performance_error_is_a_blueline_error(self):
        assert issubclass(PerformanceError, BluelineError)


class TestStanding:
    def test_a_peal_of_major_counts_as_one(self):
        assert a_performance().is_peal

    def test_something_shorter_does_not(self):
        assert not a_performance(length=1250).is_peal

    def test_it_says_what_a_quarter_is(self):
        assert a_performance(length=1250).standing.counts_as == "quarter peal"

    def test_triples_needs_the_longer_length(self):
        assert not a_performance(stage=7, length=5000).is_peal
        assert a_performance(stage=7, length=5040).is_peal


class TestCoveringTenor:
    def test_a_band_of_eight_ringing_major_covers_nothing(self):
        assert not a_performance().has_covering_tenor

    def test_a_band_of_eight_ringing_triples_covers(self):
        assert a_performance(stage=7, length=5040).has_covering_tenor


class TestWritingUp:
    def test_the_headline_names_the_place_and_the_date(self):
        assert a_performance().headline() == "St Andrew, Marchgate, 18 March 2023"

    def test_the_summary_says_what_it_counted_as(self):
        assert "a peal at" in a_performance().summary()

    def test_the_board_opens_with_the_headline(self):
        assert a_performance().board()[0] == "St Andrew, Marchgate, 18 March 2023"

    def test_the_board_names_the_length_and_the_method(self):
        assert "5024 Cambridge Surprise Major" in a_performance().board()

    def test_the_board_credits_the_composer(self):
        assert "Composed by F Ahman" in a_performance().board()

    def test_a_board_with_no_composer_leaves_the_line_out(self):
        board = a_performance(composer=None).board()
        assert not any(line.startswith("Composed") for line in board)

    def test_the_board_lists_the_band(self):
        board = a_performance().board()
        assert "1 Ann" in board
        assert "8 Hana (c)" in board

    def test_a_covering_tenor_is_noted(self):
        board = a_performance(stage=7, length=5040).board()
        assert "8 covering" in board

    def test_nothing_is_noted_when_nobody_covers(self):
        assert not any("covering" in line for line in a_performance().board())
