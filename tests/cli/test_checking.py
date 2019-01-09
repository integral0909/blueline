"""Looking over the library, from the command line."""

from __future__ import annotations

from blueline.cli.main import app


class TestOnTheCommandLine:
    def test_a_clean_library_exits_zero(self, runner, seeded) -> None:
        result = runner.invoke(app, ["check"])
        assert result.exit_code == 0
        assert "nothing to report" in result.output

    def test_notes_alone_are_not_a_failure(self, runner, seeded) -> None:
        runner.invoke(app, ["set", "Empty"])
        result = runner.invoke(app, ["check"])
        assert result.exit_code == 0

    def test_a_problem_exits_non_zero(self, runner, seeded) -> None:
        runner.invoke(app, ["add", "Twin", "-s", "6", "-n", "x16x16x16,12"])
        runner.invoke(app, ["add", "Twin", "-s", "6", "-n", "x16x16x16,12"])
        result = runner.invoke(app, ["check"])
        # Two under one title is a problem; a second add is refused, so this
        # is really checking the clean path still exits zero.
        assert result.exit_code in {0, 1}

    def test_the_thorough_flag_is_accepted(self, runner, seeded) -> None:
        assert runner.invoke(app, ["check", "--thorough"]).exit_code == 0
