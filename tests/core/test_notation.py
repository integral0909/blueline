import pytest

from blueline.core.notation import (
    Change,
    NotationError,
    apply_all,
    format_notation,
    implied_places,
    parse_change,
    parse_notation,
    split_changes,
)
from blueline.core.row import Row


class TestChange:
    def test_a_cross_swaps_every_pair(self):
        change = parse_change("x", 6)
        assert str(change.apply(Row.rounds(6))) == "214365"

    def test_places_hold_their_bells_still(self):
        change = parse_change("16", 6)
        assert str(change.apply(Row.rounds(6))) == "132546"

    def test_leading_and_seconds_at_major(self):
        change = parse_change("12", 8)
        assert str(change.apply(Row.rounds(8))) == "12436587"

    def test_writes_itself_back_out(self):
        assert str(parse_change("16", 6)) == "16"

    def test_a_cross_writes_as_x(self):
        assert str(parse_change("-", 6)) == "x"

    def test_repr_shows_the_stage(self):
        assert repr(parse_change("12", 8)) == "Change('12', stage=8)"

    def test_knows_it_is_a_cross(self):
        assert parse_change("x", 8).is_cross
        assert not parse_change("18", 8).is_cross

    def test_refuses_a_place_above_the_stage(self):
        with pytest.raises(NotationError):
            Change((1, 8), 6)

    def test_refuses_repeated_places(self):
        with pytest.raises(NotationError):
            Change((1, 1), 6)

    def test_refuses_places_out_of_order(self):
        with pytest.raises(NotationError):
            Change((6, 1), 6)

    def test_refuses_a_change_that_leaves_a_bell_unpaired(self):
        # Leading and thirds strands the second on its own.
        with pytest.raises(NotationError):
            Change((1, 3), 6)

    def test_accepts_places_that_do_pair_up_either_side(self):
        assert str(Change((1, 4), 6).apply(Row.rounds(6))) == "132465"

    def test_refuses_applying_to_the_wrong_stage(self):
        with pytest.raises(NotationError):
            parse_change("16", 6).apply(Row.rounds(8))

    def test_applying_twice_gives_the_row_back(self):
        change = parse_change("16", 6)
        row = Row.parse("135264")
        assert change.apply(change.apply(row)) == row


class TestImpliedPlaces:
    def test_leaves_a_complete_notation_alone(self):
        assert implied_places([1, 6], 6) == (1, 6)

    def test_adds_the_back_place_when_the_top_gap_is_odd(self):
        assert implied_places([3], 6) == (3, 6)

    def test_adds_the_front_place_when_the_bottom_gap_is_odd(self):
        assert implied_places([4], 6) == (1, 4)

    def test_leaves_an_even_gap_at_both_ends_alone(self):
        assert implied_places([3], 5) == (3,)

    def test_a_cross_needs_an_even_stage(self):
        assert implied_places([], 6) == ()
        with pytest.raises(NotationError):
            implied_places([], 5)

    def test_an_odd_gap_in_the_middle_is_an_error(self):
        with pytest.raises(NotationError):
            Change(implied_places([1, 3], 8), 8)


class TestSplitting:
    def test_splits_on_dots(self):
        assert split_changes("3.1.5.3") == ["3", "1", "5", "3"]

    def test_treats_a_cross_as_its_own_change(self):
        assert split_changes("x18x18") == ["x", "18", "x", "18"]

    def test_takes_a_dash_for_a_cross(self):
        assert split_changes("-18-18") == ["x", "18", "x", "18"]

    def test_ignores_an_ampersand(self):
        assert split_changes("&x18") == ["x", "18"]

    def test_copes_with_dots_around_a_cross(self):
        assert split_changes("18.x.18") == ["18", "x", "18"]


class TestParseNotation:
    def test_reads_notation_written_out_in_full(self):
        changes = parse_notation("x18x18", 8)
        assert [str(change) for change in changes] == ["x", "18", "x", "18"]

    def test_unfolds_symmetric_notation(self):
        changes = parse_notation("x16x16x16,12", 6)
        assert format_notation(changes) == "x16x16x16x16x16x12"

    def test_plain_bob_minor_is_twelve_changes(self):
        assert len(parse_notation("x16x16x16,12", 6)) == 12

    def test_plain_bob_major_is_sixteen_changes(self):
        assert len(parse_notation("x18x18x18x18,12", 8)) == 16

    def test_refuses_two_commas(self):
        with pytest.raises(NotationError):
            parse_notation("x16,12,34", 6)

    def test_refuses_nothing_before_the_comma(self):
        with pytest.raises(NotationError):
            parse_notation(",12", 6)

    def test_refuses_empty_notation(self):
        with pytest.raises(NotationError):
            parse_notation("   ", 6)

    def test_refuses_a_cross_at_an_odd_stage(self):
        with pytest.raises(NotationError):
            parse_notation("x1x1", 5)


class TestFormatting:
    def test_puts_dots_between_place_changes(self):
        changes = parse_notation("3.1.5.3", 5)
        assert format_notation(changes) == "3.1.5.3"

    def test_leaves_dots_out_around_a_cross(self):
        changes = parse_notation("x.18.x.18", 8)
        assert format_notation(changes) == "x18x18"

    def test_notation_goes_round_trip(self):
        text = "x18x18x18x18x18x18x18x12"
        assert format_notation(parse_notation(text, 8)) == text


class TestApplyAll:
    def test_gives_one_more_row_than_there_are_changes(self):
        changes = parse_notation("x16x16x16,12", 6)
        rows = apply_all(changes, Row.rounds(6))
        assert len(rows) == len(changes) + 1

    def test_starts_where_it_was_told_to(self):
        rows = apply_all(parse_notation("x16", 6), Row.rounds(6))
        assert rows[0].is_rounds

    def test_a_plain_bob_minor_lead_ends_on_its_lead_head(self):
        rows = apply_all(parse_notation("x16x16x16,12", 6), Row.rounds(6))
        assert str(rows[-1]) == "135264"

    def test_a_plain_bob_major_lead_ends_on_its_lead_head(self):
        rows = apply_all(parse_notation("x18x18x18x18,12", 8), Row.rounds(8))
        assert str(rows[-1]) == "13527486"

    def test_the_treble_hunts_up_and_down_in_plain_bob(self):
        rows = apply_all(parse_notation("x16x16x16,12", 6), Row.rounds(6))
        places = [row.place_of(1) for row in rows]
        assert places == [1, 2, 3, 4, 5, 6, 6, 5, 4, 3, 2, 1, 1]
