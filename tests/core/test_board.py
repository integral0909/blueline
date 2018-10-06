from datetime import date

import pytest

from blueline.core.bands import band_of
from blueline.core.board import WIDTH, Board, BoardError, band_lines, centred, render, rule
from blueline.core.performance import Performance
from blueline.errors import BluelineError

EIGHT = band_of(["Ann", "Bob", "Cara", "Dan", "Eve", "Finn", "Gus", "Hana"], conductor="Hana")


def a_performance(**over) -> Performance:
    fields = {
        "band": EIGHT,
        "title": "Cambridge Surprise Major",
        "stage": 8,
        "length": 5024,
        "rang_on": date(2023, 3, 18),
        "place": "St Andrew, Marchgate",
        "composer": "F Ahman",
    }
    fields.update(over)
    return Performance(**fields)


class TestCentred:
    def test_it_centres_within_the_width(self):
        assert centred("hello", width=11) == "   hello   "

    def test_it_pads_to_the_full_width(self):
        assert len(centred("hello", width=40)) == 40

    def test_it_tidies_stray_space(self):
        assert centred("  a   b  ", width=9).strip() == "a b"

    def test_it_collapses_runs_of_space(self):
        # Which is why the band lines use one space, not two.
        assert centred("1  Ann", width=20).strip() == "1 Ann"

    def test_something_too_long_is_cut_rather_than_wrapped(self):
        made = centred("x" * 100, width=20)
        assert len(made) == 20
        assert made.endswith("…")

    def test_a_width_of_nothing_is_refused(self):
        with pytest.raises(BoardError, match="some width"):
            centred("hello", width=0)

    def test_a_board_error_is_a_blueline_error(self):
        assert issubclass(BoardError, BluelineError)


class TestRule:
    def test_it_fills_the_width(self):
        assert rule(width=10) == "-" * 10

    def test_the_character_can_be_changed(self):
        assert rule(width=5, character="=") == "====="

    def test_a_rule_needs_exactly_one_character(self):
        with pytest.raises(BoardError, match="one character"):
            rule(character="--")


class TestBandLines:
    def test_one_line_per_bell(self):
        assert len(band_lines(a_performance())) == 8

    def test_each_names_the_bell_and_the_ringer(self):
        assert "1 Ann" in band_lines(a_performance())[0]

    def test_the_conductor_is_marked(self):
        assert "(c)" in band_lines(a_performance())[7]

    def test_only_the_conductor_is_marked(self):
        marked = [line for line in band_lines(a_performance()) if "(c)" in line]
        assert len(marked) == 1

    def test_every_line_is_the_full_width(self):
        assert all(len(line) == WIDTH for line in band_lines(a_performance()))


class TestRender:
    def test_it_opens_with_the_place(self):
        board = render(a_performance())
        assert "St Andrew, Marchgate" in board.lines[0]

    def test_the_date_comes_second(self):
        assert "18 March 2023" in render(a_performance()).lines[1]

    def test_it_says_what_the_length_counted_as(self):
        assert any("A peal of 5024" in line for line in render(a_performance()).lines)

    def test_a_quarter_says_so(self):
        board = render(a_performance(length=1250))
        assert any("quarter peal" in line for line in board.lines)

    def test_it_names_the_method(self):
        assert any("Cambridge Surprise Major" in line for line in render(a_performance()).lines)

    def test_it_says_how_long_it_took(self):
        assert any("h " in line for line in render(a_performance()).lines)

    def test_a_short_touch_reads_in_minutes(self):
        board = render(a_performance(length=224))
        assert any("minutes" in line for line in board.lines)

    def test_it_credits_the_composer(self):
        assert any("Composed by F Ahman" in line for line in render(a_performance()).lines)

    def test_no_composer_means_no_line(self):
        board = render(a_performance(composer=None))
        assert not any("Composed" in line for line in board.lines)

    def test_it_lists_the_band(self):
        board = render(a_performance())
        assert any("8 Hana (c)" in line for line in board.lines)

    def test_a_covering_tenor_is_noted(self):
        board = render(a_performance(stage=7, length=5040))
        assert any("8 covering" in line for line in board.lines)

    def test_nothing_is_noted_when_nobody_covers(self):
        assert not any("covering" in line for line in render(a_performance()).lines)

    def test_every_line_is_the_same_width(self):
        board = render(a_performance())
        assert {len(line) for line in board.lines} == {WIDTH}

    def test_the_width_can_be_changed(self):
        board = render(a_performance(), width=60)
        assert board.width == 60
        assert {len(line) for line in board.lines} == {60}

    def test_it_reads_as_the_lines_joined_up(self):
        board = render(a_performance())
        assert str(board).count("\n") == board.height - 1


class TestBoardShape:
    def test_a_board_knows_how_tall_it_is(self):
        made = Board(lines=("a", "b"), width=1)
        assert made.height == 2
