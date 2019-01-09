"""Compositions from the command line."""

from __future__ import annotations

from blueline.cli.main import app

PLAIN = "Plain Bob Minor"
BOBS = "---"


class TestKeeping:
    def test_a_touch_can_be_kept(self, runner, seeded) -> None:
        result = runner.invoke(app, ["keep", "A 60", PLAIN, BOBS])
        assert result.exit_code == 0
        assert "A 60" in result.output

    def test_a_composer_can_be_given(self, runner, seeded) -> None:
        result = runner.invoke(app, ["keep", "A 60", PLAIN, BOBS, "-c", "F Ahman"])
        assert "F Ahman" in result.output

    def test_a_method_nobody_has_stored(self, runner, seeded) -> None:
        result = runner.invoke(app, ["keep", "A 60", "Weasel Surprise Major", BOBS])
        assert result.exit_code != 0

    def test_a_calling_that_does_not_come_round(self, runner, seeded) -> None:
        assert runner.invoke(app, ["keep", "A 60", PLAIN, "-"]).exit_code != 0


class TestListing:
    def load(self, runner) -> None:
        runner.invoke(app, ["keep", "A 60", PLAIN, BOBS])
        runner.invoke(app, ["keep", "Another 60", PLAIN, BOBS])

    def test_nothing_stored(self, runner, seeded) -> None:
        assert "0 compositions" in runner.invoke(app, ["compositions"]).output

    def test_everything_comes_back(self, runner, seeded) -> None:
        self.load(runner)
        assert "2 compositions" in runner.invoke(app, ["compositions"]).output

    def test_by_method(self, runner, seeded) -> None:
        self.load(runner)
        result = runner.invoke(app, ["compositions", "-m", PLAIN])
        assert "2 compositions" in result.output

    def test_the_list_can_be_cut_short(self, runner, seeded) -> None:
        self.load(runner)
        assert "1 compositions" in runner.invoke(app, ["compositions", "-l", "1"]).output


class TestForgetting:
    def test_one_can_be_dropped(self, runner, seeded) -> None:
        runner.invoke(app, ["keep", "A 60", PLAIN, BOBS])
        assert runner.invoke(app, ["forget", "1"]).exit_code == 0
        assert "0 compositions" in runner.invoke(app, ["compositions"]).output

    def test_one_that_is_not_there(self, runner, seeded) -> None:
        assert runner.invoke(app, ["forget", "404"]).exit_code != 0
