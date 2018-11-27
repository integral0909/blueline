"""Comparing methods from the command line."""

from __future__ import annotations

from blueline.cli.main import app

CAMBRIDGE = "Cambridge Surprise Major"
YORKSHIRE = "Yorkshire Surprise Major"


class TestOnTheCommandLine:
    def test_two_methods_can_be_compared(self, runner, seeded) -> None:
        result = runner.invoke(app, ["against", CAMBRIDGE, YORKSHIRE])
        assert result.exit_code == 0
        assert "agree on" in result.stdout

    def test_it_says_the_share(self, runner, seeded) -> None:
        assert "%" in runner.invoke(app, ["against", CAMBRIDGE, YORKSHIRE]).stdout

    def test_the_nearest(self, runner, seeded) -> None:
        result = runner.invoke(app, ["like", CAMBRIDGE])
        assert result.exit_code == 0

    def test_two_stages(self, runner, seeded) -> None:
        assert runner.invoke(app, ["against", CAMBRIDGE, "Plain Bob Minor"]).exit_code != 0

    def test_a_method_nobody_has_stored(self, runner, seeded) -> None:
        assert runner.invoke(app, ["against", CAMBRIDGE, "Weasel Major"]).exit_code != 0
