"""Proving call change touches."""

from __future__ import annotations

from blueline.service.callchanges import how_to_get_to, prove, said
from blueline.service.results import Reason


class TestProving:
    def test_a_calling_is_rung_through(self) -> None:
        report = prove("2 to 3\n4 to 5", 8).unwrap()
        assert report.calls == 2

    def test_the_rows_include_where_they_started(self) -> None:
        report = prove("2 to 3", 8).unwrap()
        assert report.rows[0].call == "start"
        assert report.rows[0].row == "12345678"

    def test_it_says_where_they_finished(self) -> None:
        assert prove("2 to 3", 8).unwrap().finish == "13245678"

    def test_a_pair_called_back_comes_round(self) -> None:
        assert prove("2 to 3; 3 to 2", 8).unwrap().came_round is True

    def test_a_touch_that_wanders_off_does_not(self) -> None:
        assert prove("2 to 3; 4 to 5", 8).unwrap().came_round is False

    def test_ringing_nothing_is_still_rounds(self) -> None:
        assert prove("", 8).unwrap().came_round is True

    def test_a_call_that_changes_nothing_is_marked(self) -> None:
        report = prove("3 to 2", 8).unwrap()
        assert report.stood_still == 1

    def test_a_touch_can_start_anywhere(self) -> None:
        report = prove("2 to 3", 8, start="13245678").unwrap()
        assert report.start == "13245678"

    def test_a_start_on_the_wrong_number_of_bells(self) -> None:
        result = prove("2 to 3", 8, start="123456")
        assert result.failure.reason is Reason.INVALID

    def test_an_impossible_call(self) -> None:
        result = prove("2 to 5", 8)
        assert "not next to each other" in result.failure.detail

    def test_a_calling_that_does_not_parse(self) -> None:
        assert prove("stand", 8).failure.reason is Reason.INVALID

    def test_a_style_nobody_uses(self) -> None:
        assert "up or down" in prove("2 to 3", 8, style="sideways").failure.detail

    def test_devon_reads_the_pair_the_other_way(self) -> None:
        down = prove("2 to 3", 8).unwrap()
        up = prove("2 to 3", 8, style="up").unwrap()
        assert down.finish != up.finish

    def test_a_summary_reads_as_a_touch(self) -> None:
        assert prove("2 to 3", 8).unwrap().summary().startswith("1 calls")


class TestGettingSomewhere:
    def test_it_reaches_queens(self) -> None:
        report = how_to_get_to("queens", 8).unwrap()
        assert report.finish == "13572468"

    def test_the_named_change_is_noticed(self) -> None:
        assert "queens" in how_to_get_to("queens", 8).unwrap().named_reached

    def test_backrounds_takes_every_pair(self) -> None:
        assert how_to_get_to("backrounds", 8).unwrap().calls == 28

    def test_a_row_can_be_given_instead_of_a_name(self) -> None:
        assert how_to_get_to("13245678", 8).unwrap().finish == "13245678"

    def test_it_can_start_from_somewhere_else(self) -> None:
        report = how_to_get_to("rounds", 8, start="13245678").unwrap()
        assert report.came_round

    def test_somewhere_nobody_rings(self) -> None:
        assert how_to_get_to("weasels", 8).failure.reason is Reason.INVALID

    def test_a_target_on_the_wrong_number_of_bells(self) -> None:
        assert how_to_get_to("123456", 8).failure.reason is Reason.INVALID

    def test_every_call_on_the_way_is_ringable(self) -> None:
        report = how_to_get_to("tittums", 8).unwrap()
        assert len(report.rows) == report.calls + 1


class TestSaying:
    def test_it_reads_the_calls_back(self) -> None:
        report = prove("2 to 3", 8).unwrap()
        assert said(report).unwrap() == ["2 to 3"]

    def test_devon_says_it_the_other_way(self) -> None:
        report = prove("2 to 3", 8).unwrap()
        assert said(report, "up").unwrap() == ["3 to 2"]

    def test_a_call_that_did_nothing_says_stand(self) -> None:
        report = prove("3 to 2", 8).unwrap()
        assert said(report).unwrap() == ["stand"]

    def test_a_style_nobody_uses(self) -> None:
        report = prove("2 to 3", 8).unwrap()
        assert said(report, "sideways").failure.reason is Reason.INVALID

    def test_a_whole_calling_reads_back(self) -> None:
        report = how_to_get_to("queens", 8).unwrap()
        assert len(said(report).unwrap()) == report.calls
