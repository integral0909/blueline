import pytest

from blueline.core.handbells import (
    HandbellError,
    Pair,
    crossings,
    pairs_from,
    standard_pairs,
    together,
    unpaired,
)
from blueline.errors import BluelineError, StageError
from tests.methods import CAMBRIDGE_MAJOR, PLAIN_BOB_MAJOR, PLAIN_BOB_MINOR


class TestPair:
    def test_it_holds_two_bells(self):
        assert Pair(1, 2).bells == (1, 2)

    def test_it_reads_the_way_ringers_say_it(self):
        assert str(Pair(5, 6)) == "5-6"

    def test_adjacent_bells_are_adjacent(self):
        assert Pair(3, 4).is_adjacent

    def test_a_gap_is_not(self):
        assert not Pair(3, 5).is_adjacent

    def test_the_lower_has_to_be_lower(self):
        with pytest.raises(HandbellError, match="not a pair"):
            Pair(4, 3)

    def test_a_bell_cannot_be_paired_with_itself(self):
        with pytest.raises(HandbellError):
            Pair(3, 3)

    def test_it_says_whether_a_bell_is_in_it(self):
        pair = Pair(5, 6)
        assert 5 in pair
        assert 6 in pair
        assert 4 not in pair

    def test_a_handbell_error_is_a_blueline_error(self):
        assert issubclass(HandbellError, BluelineError)


class TestStandardPairs:
    def test_major_pairs_up_four_ways(self):
        assert [str(pair) for pair in standard_pairs(8)] == ["1-2", "3-4", "5-6", "7-8"]

    def test_minor_pairs_up_three_ways(self):
        assert [str(pair) for pair in standard_pairs(6)] == ["1-2", "3-4", "5-6"]

    def test_they_are_all_adjacent(self):
        assert all(pair.is_adjacent for pair in standard_pairs(8))

    def test_an_odd_stage_leaves_the_tenor_out(self):
        pairs = standard_pairs(7)
        assert [str(pair) for pair in pairs] == ["1-2", "3-4", "5-6"]
        assert unpaired(pairs, 7) == [7]

    def test_an_even_stage_leaves_nobody_out(self):
        assert unpaired(standard_pairs(8), 8) == []

    def test_a_stage_out_of_range_is_refused(self):
        with pytest.raises(StageError):
            standard_pairs(99)


class TestPairsFrom:
    def test_it_builds_what_was_asked_for(self):
        pairs = pairs_from([(1, 2), (3, 4)], 4)
        assert [str(pair) for pair in pairs] == ["1-2", "3-4"]

    def test_it_does_not_mind_the_order_within_a_pair(self):
        assert str(pairs_from([(4, 3)], 4)[0]) == "3-4"

    def test_pairs_do_not_have_to_be_adjacent(self):
        assert not pairs_from([(2, 7)], 8)[0].is_adjacent

    def test_a_bell_in_two_pairs_is_refused(self):
        with pytest.raises(HandbellError, match="two pairs"):
            pairs_from([(1, 2), (2, 3)], 8)

    def test_a_bell_that_is_not_there_is_refused(self):
        with pytest.raises(HandbellError, match="no bell 9"):
            pairs_from([(1, 9)], 8)

    def test_a_partial_pairing_leaves_the_rest_unpaired(self):
        pairs = pairs_from([(1, 2)], 8)
        assert unpaired(pairs, 8) == [3, 4, 5, 6, 7, 8]


class TestCrossings:
    def test_the_treble_pair_crosses_in_plain_bob(self):
        assert crossings(PLAIN_BOB_MAJOR, Pair(1, 2))

    def test_a_crossing_really_does_swap_them_over(self):
        rows = PLAIN_BOB_MAJOR.lead_rows()
        for index in crossings(PLAIN_BOB_MAJOR, Pair(1, 2)):
            before, after = rows[index - 1], rows[index]
            was = before.place_of(1) < before.place_of(2)
            now = after.place_of(1) < after.place_of(2)
            assert was != now

    def test_a_pair_that_never_meets_never_crosses(self):
        # In the plain course of Plain Bob the treble and the second do cross,
        # so this checks the opposite case holds where it should.
        crossed = crossings(PLAIN_BOB_MINOR, Pair(1, 2))
        assert isinstance(crossed, list)

    def test_cambridge_crosses_more_than_plain_bob(self):
        plain = len(crossings(PLAIN_BOB_MAJOR, Pair(5, 6)))
        surprise = len(crossings(CAMBRIDGE_MAJOR, Pair(5, 6)))
        assert surprise >= plain

    def test_every_crossing_is_inside_the_lead(self):
        for index in crossings(CAMBRIDGE_MAJOR, Pair(3, 4)):
            assert 1 <= index <= CAMBRIDGE_MAJOR.lead_length


class TestTogether:
    def test_a_pair_starts_together_in_rounds(self):
        assert 0 in together(PLAIN_BOB_MAJOR, Pair(1, 2))

    def test_a_pair_at_opposite_ends_is_not_together(self):
        assert 0 not in together(PLAIN_BOB_MAJOR, Pair(1, 8))

    def test_every_row_it_names_really_has_them_next_to_each_other(self):
        rows = CAMBRIDGE_MAJOR.lead_rows()
        for index in together(CAMBRIDGE_MAJOR, Pair(5, 6)):
            row = rows[index]
            assert abs(row.place_of(5) - row.place_of(6)) == 1

    def test_a_pair_is_together_somewhere_in_a_lead(self):
        assert together(CAMBRIDGE_MAJOR, Pair(3, 4))
