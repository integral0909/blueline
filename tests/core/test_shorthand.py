"""Reading a composition the way it is printed."""

from __future__ import annotations

import pytest

from blueline.core.bobs import calling_from
from blueline.core.shorthand import (
    LETTERS,
    Composition,
    ShorthandError,
    format_shorthand,
    parse_shorthand,
)
from tests.methods import PLAIN_BOB_MAJOR, PLAIN_BOB_MINOR


class TestParsing:
    def test_one_position(self) -> None:
        assert parse_shorthand("H").positions == ("Home",)

    def test_a_count_expands(self) -> None:
        assert parse_shorthand("3H").positions == ("Home", "Home", "Home")

    def test_a_count_with_a_space_in_it(self) -> None:
        assert parse_shorthand("3 H") == parse_shorthand("3H")

    def test_several_positions(self) -> None:
        assert parse_shorthand("W H H").positions == ("Wrong", "Home", "Home")

    def test_commas_are_separators(self) -> None:
        assert parse_shorthand("W, H, H") == parse_shorthand("W H H")

    def test_semicolons_are_too(self) -> None:
        assert parse_shorthand("W;H;H") == parse_shorthand("W H H")

    def test_positions_can_be_spelled_out(self) -> None:
        assert parse_shorthand("Wrong Home").positions == ("Wrong", "Home")

    def test_case_does_not_matter(self) -> None:
        assert parse_shorthand("w h") == parse_shorthand("W H")

    @pytest.mark.parametrize(("letter", "name"), sorted(LETTERS.items()))
    def test_every_letter_reads(self, letter, name) -> None:
        assert parse_shorthand(letter).positions == (name,)

    def test_in_and_out_are_both_before(self) -> None:
        assert parse_shorthand("I") == parse_shorthand("O") == parse_shorthand("B")


class TestParts:
    def test_a_times_marker(self) -> None:
        assert parse_shorthand("W H x3").parts == 3

    def test_the_word_parts(self) -> None:
        assert parse_shorthand("W H 3 parts").parts == 3

    def test_one_part(self) -> None:
        assert parse_shorthand("W H").parts == 3 - 2

    def test_a_marker_at_the_front(self) -> None:
        assert parse_shorthand("x5 W H").parts == 5

    def test_it_counts_the_calls(self) -> None:
        assert parse_shorthand("W H x3").calls == 6

    def test_expanding_gives_every_call(self) -> None:
        assert parse_shorthand("W H x3").expanded() == ("Wrong", "Home") * 3

    def test_no_parts_at_all(self) -> None:
        with pytest.raises(ShorthandError, match="cannot have 0 parts"):
            Composition(positions=("Home",), parts=0)


class TestRefusing:
    def test_nothing_to_read(self) -> None:
        with pytest.raises(ShorthandError, match="nothing to read"):
            parse_shorthand("   ")

    def test_something_that_is_not_a_position(self) -> None:
        with pytest.raises(ShorthandError, match="not a calling position"):
            parse_shorthand("W ?? H")

    def test_a_count_with_nothing_after_it(self) -> None:
        with pytest.raises(ShorthandError, match="not a calling position"):
            parse_shorthand("W H 3")

    def test_parts_but_no_calls(self) -> None:
        with pytest.raises(ShorthandError, match="not what to call"):
            parse_shorthand("x3")

    def test_a_count_of_zero(self) -> None:
        with pytest.raises(ShorthandError, match="no calls at all"):
            parse_shorthand("0H")


class TestWriting:
    def test_one_position(self) -> None:
        assert format_shorthand(parse_shorthand("H")) == "H"

    def test_a_run_is_collapsed(self) -> None:
        assert format_shorthand(parse_shorthand("H H H")) == "3H"

    def test_only_a_run_is(self) -> None:
        assert format_shorthand(parse_shorthand("W H H")) == "W 2H"

    def test_the_parts_are_written(self) -> None:
        assert format_shorthand(parse_shorthand("W H x3")) == "W H x3"

    def test_a_position_with_no_letter_keeps_its_name(self) -> None:
        assert "Fifths" in format_shorthand(parse_shorthand("Fifths"))

    def test_nothing_at_all(self) -> None:
        assert format_shorthand(Composition(positions=())) == ""

    def test_it_reads_back(self) -> None:
        for text in ("H", "W 2H", "2M W 2H x3", "W H x5"):
            assert format_shorthand(parse_shorthand(text)) == text

    def test_a_composition_prints_as_shorthand(self) -> None:
        assert str(parse_shorthand("W H H")) == "W 2H"


class TestAgainstAMethod:
    """What this produces is what core.bobs already takes."""

    def test_it_feeds_straight_into_a_calling(self) -> None:
        positions = list(parse_shorthand("W H H").positions)
        calling = calling_from(PLAIN_BOB_MAJOR, positions)
        assert calling.count("-") == 3

    def test_a_repeated_part_gives_more_calls(self) -> None:
        one = calling_from(PLAIN_BOB_MAJOR, list(parse_shorthand("W H").positions))
        three = calling_from(PLAIN_BOB_MAJOR, list(parse_shorthand("W H x3").expanded()))
        assert three.count("-") == 3 * one.count("-")

    def test_a_position_the_method_does_not_have(self) -> None:
        from blueline.core.bobs import PositionError

        positions = list(parse_shorthand("Fifths").positions)
        with pytest.raises(PositionError):
            calling_from(PLAIN_BOB_MINOR, positions)
