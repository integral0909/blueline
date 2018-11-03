"""Call change ringing."""

from __future__ import annotations

import pytest

from blueline.core.callchanges import (
    Call,
    CallChangeError,
    Style,
    apply_call,
    calling_to,
    calling_to_named,
    named_row,
    parse_call,
    parse_calling,
    ring,
)
from blueline.core.row import Row

ROUNDS = Row.rounds(8)


class TestCall:
    def test_a_call_names_two_bells(self) -> None:
        assert str(Call(moving=3, after=4)) == "3 to 4"

    def test_devon_says_it_the_other_way(self) -> None:
        assert Call(moving=3, after=4).said(Style.UP) == "4 to 3"

    def test_a_bell_cannot_be_called_after_itself(self) -> None:
        with pytest.raises(CallChangeError, match="after itself"):
            Call(moving=3, after=3)


class TestParsing:
    def test_a_written_call(self) -> None:
        assert parse_call("3 to 4") == Call(moving=3, after=4)

    def test_the_word_to_is_optional(self) -> None:
        assert parse_call("3 4") == Call(moving=3, after=4)

    def test_an_up_call_reverses_the_pair(self) -> None:
        assert parse_call("3 to 4", Style.UP) == Call(moving=4, after=3)

    def test_something_that_is_not_a_call(self) -> None:
        with pytest.raises(CallChangeError, match="is not a call"):
            parse_call("stand")

    def test_words_where_bells_belong(self) -> None:
        with pytest.raises(CallChangeError, match="two bells"):
            parse_call("treble to tenor")

    def test_a_calling_one_to_a_line(self) -> None:
        assert len(parse_calling("3 to 2\n5 to 4\n")) == 2

    def test_a_calling_separated_by_semicolons(self) -> None:
        assert len(parse_calling("3 to 2; 5 to 4")) == 2

    def test_blank_lines_are_ignored(self) -> None:
        assert len(parse_calling("3 to 2\n\n5 to 4\n")) == 2

    def test_a_whole_calling_can_be_up(self) -> None:
        calls = parse_calling("2 to 3", Style.UP)
        assert calls[0] == Call(moving=3, after=2)


class TestRinging:
    def test_a_call_swaps_an_adjacent_pair(self) -> None:
        # In rounds the 2 is in front of the 3, so putting the 2 after the 3
        # is the pair swapping.
        assert str(apply_call(ROUNDS, Call(moving=2, after=3))) == "13245678"

    def test_calling_a_pair_that_is_already_that_way_stands_still(self) -> None:
        assert apply_call(ROUNDS, Call(moving=3, after=2)) == ROUNDS

    def test_bells_that_are_not_next_to_each_other(self) -> None:
        with pytest.raises(CallChangeError, match="not next to each other"):
            apply_call(ROUNDS, Call(moving=2, after=5))

    def test_a_bell_that_is_not_ringing(self) -> None:
        with pytest.raises(CallChangeError):
            apply_call(Row.rounds(6), Call(moving=8, after=2))

    def test_ringing_a_touch_gives_every_row(self) -> None:
        calls = parse_calling("2 to 3; 4 to 5")
        assert len(ring(ROUNDS, calls)) == 3

    def test_the_first_row_is_where_they_started(self) -> None:
        assert ring(ROUNDS, parse_calling("2 to 3"))[0] == ROUNDS

    def test_ringing_nothing_leaves_them_where_they_are(self) -> None:
        assert ring(ROUNDS, ()) == [ROUNDS]


class TestCallingTo:
    def test_it_gets_there(self) -> None:
        calls = calling_to(ROUNDS, named_row("queens", 8))
        assert ring(ROUNDS, calls)[-1] == named_row("queens", 8)

    def test_queens_at_major_takes_six_calls(self) -> None:
        assert len(calling_to(ROUNDS, named_row("queens", 8))) == 6

    def test_kings_takes_twice_as_many(self) -> None:
        assert len(calling_to(ROUNDS, named_row("kings", 8))) == 12

    def test_backrounds_is_every_pair(self) -> None:
        # Eight bells, so twenty eight pairs, and a call change touch has to
        # swap each of them exactly once to turn the ring over.
        assert len(calling_to(ROUNDS, named_row("backrounds", 8))) == 28

    def test_every_call_is_one_the_band_can_ring(self) -> None:
        calls = calling_to(ROUNDS, named_row("tittums", 8))
        rows = ring(ROUNDS, calls)
        assert len(rows) == len(calls) + 1

    def test_going_nowhere_takes_no_calls(self) -> None:
        assert calling_to(ROUNDS, ROUNDS) == ()

    def test_the_rows_have_to_match(self) -> None:
        with pytest.raises(CallChangeError, match="same number of bells"):
            calling_to(ROUNDS, Row.rounds(6))

    def test_it_works_at_minor_too(self) -> None:
        rounds = Row.rounds(6)
        calls = calling_to_named(rounds, "tittums")
        assert ring(rounds, calls)[-1] == named_row("tittums", 6)


class TestNamedRows:
    def test_queens_at_major(self) -> None:
        assert str(named_row("queens", 8)) == "13572468"

    def test_kings_at_major(self) -> None:
        assert str(named_row("kings", 8)) == "75312468"

    def test_tittums_at_major(self) -> None:
        assert str(named_row("tittums", 8)) == "15263748"

    def test_names_are_not_case_sensitive(self) -> None:
        assert named_row("  Queens ", 8) == named_row("queens", 8)

    def test_something_nobody_rings_by_name(self) -> None:
        with pytest.raises(CallChangeError, match="rung by name"):
            named_row("weasels", 8)
