
from blueline.core.music import (
    NAMED_ROWS,
    backrounds,
    count_music,
    kings,
    longest_run_at_back,
    longest_run_at_front,
    name_of,
    queens,
    run_at_back,
    run_at_front,
    tittums,
)
from blueline.core.row import Row
from blueline.core.touch import plain_course
from tests.methods import CAMBRIDGE_MAJOR, PLAIN_BOB_MAJOR, PLAIN_BOB_MINOR


class TestNamedRows:
    def test_queens_at_major(self):
        assert str(queens(8)) == "13572468"

    def test_queens_at_minor(self):
        assert str(queens(6)) == "135246"

    def test_kings_is_queens_with_the_odds_turned_round(self):
        assert str(kings(8)) == "75312468"

    def test_tittums_interleaves_the_two_halves(self):
        assert str(tittums(8)) == "15263748"

    def test_tittums_at_minor(self):
        assert str(tittums(6)) == "142536"

    def test_backrounds_is_the_ring_upside_down(self):
        assert str(backrounds(8)) == "87654321"

    def test_every_named_row_is_a_real_row(self):
        for make in NAMED_ROWS.values():
            assert make(8).stage == 8

    def test_names_a_row_it_knows(self):
        assert name_of(queens(8)) == "queens"
        assert name_of(backrounds(6)) == "backrounds"
        assert name_of(Row.rounds(8)) == "rounds"

    def test_says_nothing_for_a_row_with_no_name(self):
        assert name_of(Row.parse("13527486")) is None


class TestRuns:
    def test_finds_a_run_at_the_back(self):
        assert run_at_back(Row.parse("21345678"), 4)

    def test_finds_a_run_coming_down_at_the_back(self):
        assert run_at_back(Row.parse("12348765"), 4)

    def test_finds_a_run_at_the_front(self):
        assert run_at_front(Row.parse("12348765"), 4)

    def test_says_no_when_the_bells_are_not_in_order(self):
        assert not run_at_back(Row.parse("12346857"), 4)

    def test_refuses_a_run_longer_than_the_stage(self):
        assert not run_at_back(Row.rounds(6), 8)

    def test_a_run_of_one_is_not_a_run(self):
        assert not run_at_back(Row.rounds(8), 1)

    def test_rounds_is_one_long_run(self):
        assert longest_run_at_back(Row.rounds(8)) == 8
        assert longest_run_at_front(Row.rounds(8)) == 8

    def test_backrounds_runs_the_other_way(self):
        assert longest_run_at_back(backrounds(8)) == 8

    def test_finds_the_longest_run_not_a_shorter_one(self):
        assert longest_run_at_back(Row.parse("21345678")) == 6

    def test_gives_nought_where_there_is_no_run(self):
        assert longest_run_at_back(Row.parse("13527486")) == 0


class TestCountMusic:
    def test_counts_the_named_rows_it_finds(self):
        rows = plain_course(PLAIN_BOB_MINOR).rows()[:-1]
        counted = count_music(rows)
        assert counted.named["rounds"] == 1
        assert counted.named["backrounds"] == 1

    def test_plain_bob_reaches_backrounds_at_the_half_lead(self):
        # Six changes of plain hunting at minor turns the row over completely.
        rows = plain_course(PLAIN_BOB_MINOR).rows()
        assert rows[6] == backrounds(6)

    def test_the_same_holds_at_major(self):
        rows = plain_course(PLAIN_BOB_MAJOR).rows()
        assert rows[8] == backrounds(8)

    def test_cambridge_never_reaches_backrounds_in_its_plain_course(self):
        rows = plain_course(CAMBRIDGE_MAJOR).rows()[:-1]
        assert count_music(rows).named["backrounds"] == 0

    def test_totals_the_named_rows(self):
        rows = plain_course(PLAIN_BOB_MINOR).rows()[:-1]
        assert count_music(rows).total_named == 2

    def test_counts_only_the_longest_run_in_a_row(self):
        counted = count_music([Row.parse("21345678")], min_run=4)
        assert counted.runs_at_back == {6: 1}

    def test_ignores_runs_shorter_than_asked_for(self):
        counted = count_music([Row.parse("13527486")], min_run=4)
        assert counted.runs_at_back == {}

    def test_adds_up_runs_of_at_least_a_length(self):
        rows = plain_course(CAMBRIDGE_MAJOR).rows()[:-1]
        counted = count_music(rows)
        assert counted.runs_of_at_least(4) >= counted.runs_of_at_least(5)

    def test_cambridge_has_plenty_of_four_bell_runs_at_the_back(self):
        rows = plain_course(CAMBRIDGE_MAJOR).rows()[:-1]
        assert count_music(rows).runs_of_at_least(4) > 0

    def test_counts_nothing_in_no_rows(self):
        counted = count_music([])
        assert counted.total_named == 0
        assert counted.runs_of_at_least(4) == 0
