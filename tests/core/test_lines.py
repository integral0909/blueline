import pytest

from blueline.core.lines import (
    Segment,
    describe_path,
    grid,
    leads_of_course,
    line_of,
    marked_grid,
    path_segments,
    place_bell_order,
)
from tests.methods import CAMBRIDGE_MINOR, PLAIN_BOB_MAJOR, PLAIN_BOB_MINOR


class TestSegment:
    def test_a_stretch_in_one_place_counts_both_blows(self):
        segment = Segment(start_row=5, end_row=6, start_place=6, end_place=6)
        assert segment.blows == 2
        assert segment.is_still

    def test_a_single_row_is_one_blow(self):
        assert Segment(start_row=3, end_row=3, start_place=2, end_place=2).blows == 1

    def test_it_knows_which_way_it_is_going(self):
        assert Segment(start_row=0, end_row=5, start_place=1, end_place=6).going_up
        assert not Segment(start_row=0, end_row=5, start_place=6, end_place=1).going_up

    def test_a_run_reads_as_a_run(self):
        assert str(Segment(0, 5, 1, 6)) == "1 to 6 up"

    def test_places_read_as_blows(self):
        assert str(Segment(5, 6, 6, 6)) == "2 blows in 6"


class TestPathSegments:
    def test_the_treble_hunts_up_lies_hunts_down_and_leads(self):
        assert describe_path(PLAIN_BOB_MINOR.path_of(1)) == (
            "1 to 6 up, 2 blows in 6, 6 to 1 down, 2 blows in 1"
        )

    def test_the_second_leads_first(self):
        assert describe_path(PLAIN_BOB_MINOR.path_of(2)).startswith("2 to 1 down, 2 blows in 1")

    def test_a_short_path_has_no_segments(self):
        assert path_segments((3,)) == []
        assert path_segments(()) == []

    def test_a_path_of_two_is_one_segment(self):
        assert len(path_segments((1, 2))) == 1

    def test_nothing_to_describe_reads_as_nothing(self):
        assert describe_path((3,)) == "nothing"

    def test_the_segments_cover_the_whole_path(self):
        path = CAMBRIDGE_MINOR.path_of(3)
        segments = path_segments(path)
        assert segments[0].start_row == 0
        assert segments[-1].end_row == len(path) - 1

    def test_the_segments_join_up(self):
        segments = path_segments(CAMBRIDGE_MINOR.path_of(4))
        for earlier, later in zip(segments, segments[1:]):
            assert earlier.end_row == later.start_row
            assert earlier.end_place == later.start_place


class TestGrid:
    def test_a_grid_is_one_line_per_row(self):
        rows = PLAIN_BOB_MINOR.lead_rows()
        assert len(grid(rows)) == len(rows)

    def test_each_line_is_the_row_written_out(self):
        assert grid(PLAIN_BOB_MINOR.lead_rows())[0] == "123456"

    def test_marking_puts_a_star_where_the_bell_is(self):
        marked = marked_grid(PLAIN_BOB_MINOR.lead_rows(), 2)
        assert marked[0] == "1*3456"

    def test_the_mark_follows_the_bell_down(self):
        marked = marked_grid(PLAIN_BOB_MINOR.lead_rows(), 2)
        assert marked[1].index("*") == 0

    def test_every_line_has_exactly_one_mark(self):
        for line in marked_grid(CAMBRIDGE_MINOR.lead_rows(), 5):
            assert line.count("*") == 1

    def test_the_mark_can_be_something_else(self):
        assert marked_grid(PLAIN_BOB_MINOR.lead_rows(), 1, mark="o")[0] == "o23456"

    def test_it_refuses_a_mark_of_more_than_one_character(self):
        with pytest.raises(ValueError, match="single character"):
            marked_grid(PLAIN_BOB_MINOR.lead_rows(), 1, mark="**")


class TestLine:
    def test_a_line_is_the_places_a_bell_rings_in(self):
        assert line_of(PLAIN_BOB_MINOR, 1)[:4] == [1, 2, 3, 4]

    def test_it_is_as_long_as_the_lead(self):
        assert len(line_of(CAMBRIDGE_MINOR, 3)) == CAMBRIDGE_MINOR.lead_length + 1


class TestLeadsOfCourse:
    def test_there_are_as_many_leads_as_the_course_has(self):
        leads = leads_of_course(PLAIN_BOB_MINOR)
        assert len(leads) == PLAIN_BOB_MINOR.leads_in_course

    def test_the_first_lead_starts_at_rounds(self):
        assert leads_of_course(PLAIN_BOB_MINOR)[0][0].is_rounds

    def test_the_last_lead_ends_at_rounds(self):
        assert leads_of_course(PLAIN_BOB_MINOR)[-1][-1].is_rounds

    def test_each_lead_starts_where_the_one_before_ended(self):
        leads = leads_of_course(CAMBRIDGE_MINOR)
        for earlier, later in zip(leads, leads[1:]):
            assert earlier[-1] == later[0]


class TestPlaceBells:
    def test_plain_bob_minor_runs_two_four_six_five_three(self):
        assert place_bell_order(PLAIN_BOB_MINOR) == [2, 4, 6, 5, 3]

    def test_plain_bob_major_runs_two_four_six_eight_seven_five_three(self):
        assert place_bell_order(PLAIN_BOB_MAJOR) == [2, 4, 6, 8, 7, 5, 3]

    def test_there_is_one_for_each_lead(self):
        assert len(place_bell_order(CAMBRIDGE_MINOR)) == CAMBRIDGE_MINOR.leads_in_course

    def test_every_working_place_is_visited_once(self):
        order = place_bell_order(PLAIN_BOB_MAJOR)
        assert sorted(order) == list(range(2, 9))

    def test_it_starts_at_the_second(self):
        assert place_bell_order(CAMBRIDGE_MINOR)[0] == 2
