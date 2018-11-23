"""Named sets of methods, from the command line."""

from __future__ import annotations

import pytest

from blueline.cli.main import app

MINOR = ["-m", "Plain Bob Minor", "-m", "Cambridge Surprise Minor"]


@pytest.fixture()
def kept(runner, seeded):
    runner.invoke(app, ["set", "Tuesday", *MINOR, "--note", "working on"])
    return runner


class TestSet:
    def test_a_set_can_be_written_down(self, runner, seeded) -> None:
        result = runner.invoke(app, ["set", "Tuesday", *MINOR])
        assert result.exit_code == 0
        assert "Tuesday" in result.stdout

    def test_the_same_name_twice(self, kept) -> None:
        assert kept.invoke(app, ["set", "Tuesday", *MINOR]).exit_code != 0


class TestSets:
    def test_it_lists_the_named_ones_too(self, runner, seeded) -> None:
        assert "3 sets" in runner.invoke(app, ["sets"]).stdout

    def test_they_can_be_left_out(self, kept) -> None:
        assert "1 sets" in kept.invoke(app, ["sets", "--mine"]).stdout


class TestShow:
    def test_it_shows_what_is_in_one(self, kept) -> None:
        result = kept.invoke(app, ["show-set", "Tuesday"])
        assert "Cambridge Surprise Minor" in result.stdout

    def test_a_named_set_needs_no_storing(self, runner, seeded) -> None:
        result = runner.invoke(app, ["show-set", "the standard eight"])
        assert result.exit_code == 0

    def test_a_name_nobody_uses(self, runner, seeded) -> None:
        assert runner.invoke(app, ["show-set", "the weasel four"]).exit_code != 0


class TestChanging:
    def test_a_method_can_be_added(self, kept) -> None:
        result = kept.invoke(app, ["set-add", "Tuesday", "Grandsire Doubles"])
        assert result.exit_code == 0
        assert "Grandsire Doubles" in result.stdout

    def test_a_method_can_be_taken_out(self, kept) -> None:
        result = kept.invoke(app, ["set-drop", "Tuesday", "Plain Bob Minor"])
        assert result.exit_code == 0

    def test_one_can_be_forgotten(self, kept) -> None:
        assert kept.invoke(app, ["forget-set", "Tuesday"]).exit_code == 0
        assert "0 sets" in kept.invoke(app, ["sets", "--mine"]).stdout

    def test_forgetting_one_that_is_not_there(self, kept) -> None:
        assert kept.invoke(app, ["forget-set", "Nothing"]).exit_code != 0


class TestCovers:
    def test_what_the_band_covers(self, kept) -> None:
        kept.invoke(app, ["ringer", "Ann", "-r", "Plain Bob Minor"])
        result = kept.invoke(app, ["covers", "Tuesday"])
        assert result.exit_code == 0
        assert "1 of 2" in result.stdout

    def test_what_one_ringer_covers(self, kept) -> None:
        kept.invoke(app, ["ringer", "Ann", "-r", "Plain Bob Minor"])
        result = kept.invoke(app, ["covers", "Tuesday", "-w", "Ann"])
        assert "50%" in result.stdout

    def test_a_ringer_nobody_has_heard_of(self, kept) -> None:
        assert kept.invoke(app, ["covers", "Tuesday", "-w", "Nobody"]).exit_code != 0
