"""Call changes from the command line."""

from __future__ import annotations

import pytest

from blueline.cli.main import app


@pytest.fixture()
def calling(tmp_path):
    path = tmp_path / "calling.txt"
    path.write_text("2 to 3\n4 to 5\n")
    return path


class TestCalls:
    def test_a_calling_is_rung_through(self, runner) -> None:
        result = runner.invoke(app, ["calls", "2 to 3; 4 to 5", "8"])
        assert result.exit_code == 0
        assert "2 calls" in result.stdout

    def test_the_rows_can_be_shown(self, runner) -> None:
        result = runner.invoke(app, ["calls", "2 to 3", "8", "--rows"])
        assert "12345678" in result.stdout

    def test_a_start_can_be_given(self, runner) -> None:
        result = runner.invoke(app, ["calls", "2 to 3", "8", "--from", "13245678"])
        assert result.exit_code == 0

    def test_an_impossible_call(self, runner) -> None:
        result = runner.invoke(app, ["calls", "2 to 5", "8"])
        assert result.exit_code != 0

    def test_a_style_nobody_uses(self, runner) -> None:
        result = runner.invoke(app, ["calls", "2 to 3", "8", "--style", "sideways"])
        assert result.exit_code != 0


class TestCallsFile:
    def test_a_written_calling(self, runner, calling) -> None:
        result = runner.invoke(app, ["calls-file", str(calling), "8"])
        assert result.exit_code == 0
        assert "2 calls" in result.stdout

    def test_a_missing_file(self, runner, tmp_path) -> None:
        result = runner.invoke(app, ["calls-file", str(tmp_path / "gone.txt"), "8"])
        assert result.exit_code != 0


class TestRoute:
    def test_getting_to_queens(self, runner) -> None:
        result = runner.invoke(app, ["route", "queens", "8"])
        assert result.exit_code == 0
        assert "13572468" in result.stdout

    def test_the_calls_are_listed(self, runner) -> None:
        result = runner.invoke(app, ["route", "queens", "8"])
        assert result.stdout.count(" to ") >= 6

    def test_devon_says_them_the_other_way(self, runner) -> None:
        down = runner.invoke(app, ["route", "queens", "8"]).stdout
        up = runner.invoke(app, ["route", "queens", "8", "--style", "up"]).stdout
        assert down != up

    def test_somewhere_nobody_rings(self, runner) -> None:
        assert runner.invoke(app, ["route", "weasels", "8"]).exit_code != 0
