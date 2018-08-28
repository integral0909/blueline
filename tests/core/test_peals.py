import pytest

from blueline.core.peals import (
    PEAL,
    PEAL_LENGTHS,
    QUARTER,
    TOUCH,
    extents_in,
    is_peal,
    is_quarter,
    peal_length,
    quarter_length,
    standing_of,
)
from blueline.core.stage import MAX_STAGE, MIN_STAGE
from blueline.errors import StageError


class TestPealLengths:
    def test_seven_bells_and_fewer_want_five_thousand_and_forty(self):
        for stage in range(3, 8):
            assert peal_length(stage) == 5040

    def test_eight_and_more_want_five_thousand(self):
        for stage in range(8, MAX_STAGE + 1):
            assert peal_length(stage) == 5000

    def test_every_stage_has_a_length(self):
        for stage in range(MIN_STAGE, MAX_STAGE + 1):
            assert stage in PEAL_LENGTHS

    def test_a_stage_out_of_range_is_refused(self):
        with pytest.raises(StageError):
            peal_length(99)

    def test_a_peal_of_triples_is_exactly_an_extent(self):
        from blueline.core.truth import extent_length

        assert peal_length(7) == extent_length(7)


class TestQuarters:
    def test_a_quarter_of_triples_is_twelve_sixty(self):
        assert quarter_length(7) == 1260

    def test_a_quarter_of_major_is_twelve_fifty(self):
        assert quarter_length(8) == 1250

    def test_it_is_a_quarter_of_the_peal_length(self):
        for stage in range(MIN_STAGE, MAX_STAGE + 1):
            assert quarter_length(stage) * 4 == peal_length(stage)


class TestStanding:
    def test_a_full_peal_counts_as_one(self):
        assert standing_of(5000, 8).counts_as == PEAL

    def test_one_change_over_still_counts(self):
        assert standing_of(5001, 8).is_peal

    def test_one_change_under_does_not(self):
        assert not standing_of(4999, 8).is_peal

    def test_a_quarter_counts_as_a_quarter(self):
        assert standing_of(1250, 8).counts_as == QUARTER

    def test_anything_shorter_is_just_a_touch(self):
        assert standing_of(224, 8).counts_as == TOUCH

    def test_a_peal_is_short_by_nothing(self):
        assert standing_of(5000, 8).short_by == 0

    def test_a_quarter_says_how_far_off_a_peal_it_is(self):
        assert standing_of(1250, 8).short_by == 3750

    def test_a_touch_says_how_far_off_a_quarter_it_is(self):
        assert standing_of(224, 8).short_by == 1026

    def test_a_peal_reads_as_a_peal(self):
        assert str(standing_of(5040, 6)) == "5040 changes, a peal"

    def test_something_short_says_what_it_is_short_of(self):
        assert "short of a peal" in str(standing_of(1250, 8))

    def test_a_short_touch_is_short_of_a_quarter(self):
        assert "short of a quarter peal" in str(standing_of(224, 8))

    def test_a_quarter_is_not_a_peal_and_the_other_way_round(self):
        quarter = standing_of(1250, 8)
        assert quarter.is_quarter
        assert not quarter.is_peal


class TestHelpers:
    def test_is_peal_agrees_with_the_standing(self):
        assert is_peal(5000, 8)
        assert not is_peal(4999, 8)

    def test_is_quarter_excludes_a_full_peal(self):
        assert is_quarter(1250, 8)
        assert not is_quarter(5000, 8)

    def test_is_quarter_excludes_a_short_touch(self):
        assert not is_quarter(224, 8)


class TestExtents:
    def test_a_peal_of_minor_is_seven_extents_exactly(self):
        assert extents_in(5040, 6) == (7, 0)

    def test_a_peal_of_triples_is_one_extent(self):
        assert extents_in(5040, 7) == (1, 0)

    def test_a_plain_course_of_major_is_no_extents_at_all(self):
        whole, over = extents_in(224, 8)
        assert whole == 0
        assert over == 224

    def test_a_length_that_does_not_divide_says_what_is_left(self):
        whole, over = extents_in(5000, 6)
        assert whole == 6
        assert over == 5000 - 6 * 720
