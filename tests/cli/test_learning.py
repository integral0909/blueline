"""What to learn next, from the command line."""

from __future__ import annotations

import pytest

from blueline.cli.main import app


@pytest.fixture()
def band(runner, seeded):
    runner.invoke(app, ["ringer", "Ann", "-r", "Plain Bob Doubles"])
    runner.invoke(app, ["ringer", "Bob", "-r", "Plain Bob Doubles", "-r", "Plain Bob Minor"])
    return runner


class TestOrder:
    def test_it_lists_the_library_in_order(self, runner, seeded) -> None:
        result = runner.invoke(app, ["order"])
        assert result.exit_code == 0
        assert "Plain Bob Doubles" in result.stdout

    def test_it_can_be_narrowed_to_a_stage(self, runner, seeded) -> None:
        assert runner.invoke(app, ["order", "-s", "6"]).exit_code == 0


class TestHard:
    def test_it_scores_a_method(self, runner, seeded) -> None:
        result = runner.invoke(app, ["hard", "Cambridge Surprise Minor"])
        assert result.exit_code == 0
        assert "Cambridge" in result.stdout

    def test_a_method_nobody_has_stored(self, runner, seeded) -> None:
        assert runner.invoke(app, ["hard", "Weasel Surprise Major"]).exit_code != 0


class TestNext:
    def test_it_advises_a_ringer(self, band) -> None:
        result = band.invoke(app, ["next", "Ann"])
        assert result.exit_code == 0
        assert "Ann" in result.stdout

    def test_it_says_what_to_go_on_to(self, band) -> None:
        assert "could go on to" in band.invoke(app, ["next", "Bob"]).stdout

    def test_a_ringer_nobody_has_heard_of(self, band) -> None:
        assert band.invoke(app, ["next", "Nobody"]).exit_code != 0


class TestBandNext:
    def test_it_advises_the_band(self, band) -> None:
        result = band.invoke(app, ["band-next"])
        assert result.exit_code == 0

    def test_nobody_on_the_books(self, runner, seeded) -> None:
        assert runner.invoke(app, ["band-next"]).exit_code != 0
