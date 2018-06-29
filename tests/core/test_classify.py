import pytest

from blueline.core.classify import (
    Classification,
    blows_per_place,
    classify,
    cross_section_indices,
    has_internal_places,
    internal_places_at_cross_sections,
    internal_places_away_from_the_treble,
    treble_dodges,
    treble_hunts_plainly,
)
from blueline.core.notation import parse_change
from tests.methods import (
    CAMBRIDGE_MAJOR,
    CAMBRIDGE_MINOR,
    GRANDSIRE_DOUBLES,
    NO_HUNT_BELL,
    PLAIN_BOB_MAJOR,
    PLAIN_BOB_MINOR,
    method_id,
)


class TestClassificationText:
    def test_reads_as_the_kind_on_its_own(self):
        assert str(Classification("Surprise")) == "Surprise"

    def test_reads_with_a_family_in_front(self):
        assert str(Classification("Bob", family="Little")) == "Little Bob"


class TestTreblePath:
    def test_plain_bob_gives_the_treble_two_blows_everywhere(self):
        assert set(blows_per_place(PLAIN_BOB_MINOR).values()) == {2}

    def test_cambridge_gives_the_treble_four_blows_everywhere(self):
        assert set(blows_per_place(CAMBRIDGE_MINOR).values()) == {4}

    def test_the_treble_visits_every_place(self):
        assert set(blows_per_place(CAMBRIDGE_MAJOR)) == set(range(1, 9))

    def test_recognises_plain_hunting(self):
        assert treble_hunts_plainly(PLAIN_BOB_MINOR)
        assert treble_hunts_plainly(GRANDSIRE_DOUBLES)

    def test_does_not_call_a_dodging_treble_plain(self):
        assert not treble_hunts_plainly(CAMBRIDGE_MINOR)

    def test_recognises_a_dodging_treble(self):
        assert treble_dodges(CAMBRIDGE_MINOR)
        assert treble_dodges(CAMBRIDGE_MAJOR)

    def test_does_not_call_a_plain_treble_dodging(self):
        assert not treble_dodges(PLAIN_BOB_MINOR)


class TestInternalPlaces:
    def test_seconds_at_major_is_internal(self):
        assert has_internal_places(parse_change("12", 8))

    def test_the_front_and_back_are_not_internal(self):
        assert not has_internal_places(parse_change("18", 8))

    def test_a_cross_makes_no_places_at_all(self):
        assert not has_internal_places(parse_change("x", 8))

    def test_plain_bob_only_makes_seconds_at_the_lead_end(self):
        assert not internal_places_away_from_the_treble(PLAIN_BOB_MINOR)

    def test_grandsire_only_makes_thirds_as_the_treble_leaves_the_lead(self):
        assert not internal_places_away_from_the_treble(GRANDSIRE_DOUBLES)


class TestCrossSections:
    def test_cambridge_minor_has_four_cross_sections(self):
        assert cross_section_indices(CAMBRIDGE_MINOR) == [3, 7, 15, 19]

    def test_cambridge_makes_places_at_every_one(self):
        assert internal_places_at_cross_sections(CAMBRIDGE_MINOR) == [True] * 4

    def test_cambridge_major_has_six(self):
        assert len(cross_section_indices(CAMBRIDGE_MAJOR)) == 6


class TestClassify:
    def test_plain_bob_is_a_bob_method(self):
        assert str(classify(PLAIN_BOB_MINOR)) == "Bob"
        assert str(classify(PLAIN_BOB_MAJOR)) == "Bob"

    def test_grandsire_is_a_bob_method_with_two_hunt_bells(self):
        assert str(classify(GRANDSIRE_DOUBLES)) == "Bob"
        assert GRANDSIRE_DOUBLES.hunt_bells == (1, 2)

    def test_cambridge_is_surprise(self):
        assert str(classify(CAMBRIDGE_MINOR)) == "Surprise"

    def test_cambridge_major_is_surprise_too(self):
        assert str(classify(CAMBRIDGE_MAJOR)) == "Surprise"

    def test_cambridge_major_has_a_thirty_two_row_lead(self):
        assert CAMBRIDGE_MAJOR.lead_length == 32

    def test_a_method_with_nothing_fixed_is_a_principle(self):
        assert NO_HUNT_BELL.hunt_bells == ()
        assert str(classify(NO_HUNT_BELL)) == "Principle"

    @pytest.mark.parametrize(
        "method",
        [PLAIN_BOB_MINOR, PLAIN_BOB_MAJOR, GRANDSIRE_DOUBLES, CAMBRIDGE_MINOR, CAMBRIDGE_MAJOR],
        ids=method_id,
    )
    def test_every_real_method_gets_a_class(self, method):
        assert str(classify(method))
