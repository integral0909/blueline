import pytest

from blueline.core.calls import plain_bob_calls
from blueline.core.rounds import (
    RoundsAt,
    comes_round_early,
    ends_at_a_lead_end,
    find_rounds,
    rounds_in_the_middle,
)
from blueline.core.row import Row
from blueline.core.touch import parse_calling, plain_course, repeat
from tests.methods import PLAIN_BOB_MINOR

PB6 = plain_bob_calls(6)
LEAD = PLAIN_BOB_MINOR.lead_length


class TestFindRounds:
    def test_the_opening_row_is_skipped(self):
        rows = plain_course(PLAIN_BOB_MINOR).rows()
        found = find_rounds(rows, LEAD)
        assert all(entry.row != 0 for entry in found)

    def test_it_finds_the_closing_rounds(self):
        rows = plain_course(PLAIN_BOB_MINOR).rows()
        assert [entry.row for entry in find_rounds(rows, LEAD)] == [60]

    def test_the_closing_rounds_is_at_a_lead_end(self):
        rows = plain_course(PLAIN_BOB_MINOR).rows()
        assert find_rounds(rows, LEAD)[0].at_lead_end

    def test_it_says_which_lead(self):
        rows = plain_course(PLAIN_BOB_MINOR).rows()
        assert find_rounds(rows, LEAD)[0].lead == 5

    def test_the_opening_can_be_kept_if_asked(self):
        rows = plain_course(PLAIN_BOB_MINOR).rows()
        assert find_rounds(rows, LEAD, skip_opening=False)[0].row == 0

    def test_ringing_a_course_twice_finds_rounds_twice(self):
        rows = repeat(plain_course(PLAIN_BOB_MINOR), 2).rows()
        assert [entry.row for entry in find_rounds(rows, LEAD)] == [60, 120]

    def test_a_lead_length_of_nothing_is_refused(self):
        with pytest.raises(ValueError, match="at least one row"):
            find_rounds([Row.rounds(6)], 0)

    def test_no_rows_finds_nothing(self):
        assert find_rounds([], LEAD) == []


class TestComesRoundEarly:
    def test_a_plain_course_does_not(self):
        rows = plain_course(PLAIN_BOB_MINOR).rows()
        assert comes_round_early(rows, LEAD) is None

    def test_ringing_it_twice_does(self):
        rows = repeat(plain_course(PLAIN_BOB_MINOR), 2).rows()
        early = comes_round_early(rows, LEAD)
        assert early is not None
        assert early.row == 60

    def test_it_says_which_lead_it_happened_at(self):
        rows = repeat(plain_course(PLAIN_BOB_MINOR), 2).rows()
        assert comes_round_early(rows, LEAD).lead == 5

    def test_a_touch_that_never_comes_round_reports_nothing(self):
        rows = parse_calling(PLAIN_BOB_MINOR, PB6, "--").rows()
        assert comes_round_early(rows, LEAD) is None


class TestStandingPlaces:
    def test_a_plain_course_ends_where_a_band_could_stand(self):
        rows = plain_course(PLAIN_BOB_MINOR).rows()
        assert ends_at_a_lead_end(rows, LEAD)

    def test_stopping_part_way_through_a_lead_does_not(self):
        rows = plain_course(PLAIN_BOB_MINOR).rows()[:-3]
        assert not ends_at_a_lead_end(rows, LEAD)

    def test_no_rows_at_all_is_not_a_place_to_stand(self):
        assert not ends_at_a_lead_end([], LEAD)

    def test_a_plain_course_never_has_rounds_mid_lead(self):
        rows = plain_course(PLAIN_BOB_MINOR).rows()
        assert rounds_in_the_middle(rows, LEAD) == []

    def test_rounds_mid_lead_is_reported(self):
        # Rounds dropped into the middle of a lead on purpose.
        rows = plain_course(PLAIN_BOB_MINOR).rows()
        doctored = [*rows[:6], Row.rounds(6), *rows[7:]]
        found = rounds_in_the_middle(doctored, LEAD)
        assert [entry.row for entry in found] == [6]
        assert not found[0].at_lead_end


class TestText:
    def test_a_lead_end_reads_as_one(self):
        assert "at the lead end" in str(RoundsAt(row=60, lead=5, at_lead_end=True))

    def test_the_middle_of_a_lead_reads_differently(self):
        assert "part way through" in str(RoundsAt(row=6, lead=1, at_lead_end=False))

    def test_it_names_the_row_and_the_lead(self):
        text = str(RoundsAt(row=60, lead=5, at_lead_end=True))
        assert "row 60" in text
        assert "lead 5" in text
