import pytest

from blueline.analysis import MethodReport, analyse, compare
from tests.methods import (
    ALL_METHODS,
    CAMBRIDGE_MAJOR,
    CAMBRIDGE_MINOR,
    COURSE_LENGTHS,
    GRANDSIRE_DOUBLES,
    NO_HUNT_BELL,
    PLAIN_BOB_MAJOR,
    PLAIN_BOB_MINOR,
    method_id,
)


class TestTitles:
    def test_plain_bob_minor(self):
        assert str(analyse(PLAIN_BOB_MINOR).title) == "Plain Bob Minor"

    def test_cambridge_surprise_major(self):
        assert str(analyse(CAMBRIDGE_MAJOR).title) == "Cambridge Surprise Major"

    def test_grandsire_keeps_its_class_out_of_the_title(self):
        assert str(analyse(GRANDSIRE_DOUBLES).title) == "Grandsire Doubles"

    def test_a_name_can_be_given_at_the_time(self):
        assert str(analyse(CAMBRIDGE_MINOR, name="Primrose").title) == "Primrose Surprise Minor"


class TestReport:
    @pytest.mark.parametrize("method", ALL_METHODS, ids=method_id)
    def test_every_method_gets_a_report(self, method):
        assert isinstance(analyse(method), MethodReport)

    @pytest.mark.parametrize("method", ALL_METHODS, ids=method_id)
    def test_the_notation_survives_the_trip(self, method):
        assert analyse(method).notation == method.notation

    @pytest.mark.parametrize("method", ALL_METHODS, ids=method_id)
    def test_the_plain_course_is_true(self, method):
        assert analyse(method).course_is_true

    def test_course_lengths_match_the_books(self):
        for method in ALL_METHODS:
            key = method_id(method)
            if key in COURSE_LENGTHS:
                assert analyse(method).course_length == COURSE_LENGTHS[key]

    def test_it_carries_the_lead_head(self):
        assert str(analyse(PLAIN_BOB_MINOR).lead_head) == "135264"

    def test_it_carries_the_coursing_order(self):
        assert analyse(PLAIN_BOB_MAJOR).coursing_order == (8, 7, 5, 3, 2, 4, 6)

    def test_hunt_and_working_bells_cover_the_stage(self):
        report = analyse(CAMBRIDGE_MINOR)
        assert set(report.hunt_bells) | set(report.working_bells) == set(range(1, 7))

    def test_it_says_which_family(self):
        assert str(analyse(CAMBRIDGE_MINOR).classification) == "Surprise"

    def test_it_says_what_symmetry(self):
        assert analyse(CAMBRIDGE_MINOR).symmetry == "palindromic"

    def test_it_counts_the_music_in_the_plain_course(self):
        assert analyse(PLAIN_BOB_MINOR).music.named["backrounds"] == 1


class TestPrinciples:
    def test_a_principle_is_flagged(self):
        assert analyse(NO_HUNT_BELL).is_principle

    def test_a_method_with_a_hunt_bell_is_not(self):
        assert not analyse(PLAIN_BOB_MINOR).is_principle

    def test_a_principle_has_no_coursing_order(self):
        # Nothing is hunting, so there is nothing for the rest to course past.
        assert analyse(NO_HUNT_BELL).coursing_order == ()


class TestCoveringTenor:
    def test_doubles_covers(self):
        assert analyse(GRANDSIRE_DOUBLES).has_covering_tenor

    def test_minor_does_not(self):
        assert not analyse(PLAIN_BOB_MINOR).has_covering_tenor


class TestHeadline:
    def test_it_names_the_method_and_its_shape(self):
        line = analyse(PLAIN_BOB_MINOR).headline()
        assert line.startswith("Plain Bob Minor")
        assert "lead 12" in line
        assert "course 60" in line


class TestCompare:
    def test_a_method_against_itself_differs_nowhere(self):
        assert compare(PLAIN_BOB_MINOR, PLAIN_BOB_MINOR) == {}

    def test_it_finds_the_class_difference(self):
        differences = compare(PLAIN_BOB_MINOR, CAMBRIDGE_MINOR)
        assert differences["class"] == ("Bob", "Surprise")

    def test_it_finds_the_lead_length_difference(self):
        differences = compare(PLAIN_BOB_MINOR, CAMBRIDGE_MINOR)
        assert differences["lead length"] == (12, 24)

    def test_it_leaves_out_what_is_the_same(self):
        differences = compare(PLAIN_BOB_MINOR, CAMBRIDGE_MINOR)
        assert "stage" not in differences

    def test_two_stages_of_the_same_method_differ_by_stage(self):
        differences = compare(PLAIN_BOB_MINOR, PLAIN_BOB_MAJOR)
        assert differences["stage"] == (6, 8)
        assert "class" not in differences
