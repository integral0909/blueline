from blueline.cli.commands.common import EXIT_FOR
from blueline.cli.main import app
from blueline.service.results import Reason


class TestPlan:
    def test_it_plans_a_practice(self, runner, seeded):
        result = runner.invoke(app, ["plan", "8", "60"])
        assert result.exit_code == 0
        assert "8 ringers" in result.stdout

    def test_it_names_what_to_ring(self, runner, seeded):
        result = runner.invoke(app, ["plan", "8", "60"])
        assert " of " in result.stdout

    def test_it_says_what_is_spare(self, runner, seeded):
        result = runner.invoke(app, ["plan", "8", "60"])
        assert "to spare" in result.stdout

    def test_a_tower_caps_the_band(self, runner, seeded):
        runner.invoke(app, ["tower", "St Mary, Ashcombe", "-b", "6", "-t", "8-0-0"])
        result = runner.invoke(app, ["plan", "8", "60", "-p", "St Mary, Ashcombe"])
        assert "6 ringers" in result.stdout

    def test_a_tower_that_is_not_there_exits_not_found(self, runner, seeded):
        result = runner.invoke(app, ["plan", "8", "60", "-p", "Nowhere"])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]

    def test_a_band_too_small_exits_invalid(self, runner, seeded):
        result = runner.invoke(app, ["plan", "2", "60"])
        assert result.exit_code == EXIT_FOR[Reason.INVALID]

    def test_a_practice_of_no_time_exits_invalid(self, runner, seeded):
        result = runner.invoke(app, ["plan", "8", "0"])
        assert result.exit_code == EXIT_FOR[Reason.INVALID]


class TestRingable:
    def test_it_lists_what_a_band_could_ring(self, runner, seeded):
        result = runner.invoke(app, ["ringable", "8"])
        assert result.exit_code == 0
        assert "Cambridge 8" in result.stdout

    def test_it_leaves_out_what_they_cannot(self, runner, seeded):
        result = runner.invoke(app, ["ringable", "8"])
        assert "Cambridge 6" not in result.stdout

    def test_a_band_too_small_exits_invalid(self, runner, seeded):
        result = runner.invoke(app, ["ringable", "2"])
        assert result.exit_code == EXIT_FOR[Reason.INVALID]


class TestByAbility:
    def _band(self, runner):
        for name in ("Ann", "Bob", "Cara", "Dan", "Eve", "Finn"):
            runner.invoke(
                app,
                ["ringer", name, "-r", "Plain Bob Major", "-r", "Cambridge Surprise Major"],
            )
        runner.invoke(
            app, ["ringer", "Gus", "-r", "Plain Bob Major", "-l", "Cambridge Surprise Major"]
        )
        runner.invoke(app, ["ringer", "Hana", "-r", "Plain Bob Major"])

    def test_it_only_picks_what_the_band_can_get_through(self, runner, seeded):
        self._band(runner)
        result = runner.invoke(app, ["plan", "8", "60"])
        assert result.exit_code == 0
        assert "Plain" in result.stdout

    def test_it_says_how_much_was_left_out(self, runner, seeded):
        self._band(runner)
        result = runner.invoke(app, ["plan", "8", "60"])
        assert "beyond the band" in result.stdout

    def test_it_can_be_told_to_ignore_the_band(self, runner, seeded):
        self._band(runner)
        result = runner.invoke(app, ["plan", "8", "60", "--anything"])
        assert "beyond the band" not in result.stdout

    def test_with_nobody_stored_nothing_is_filtered(self, runner, seeded):
        result = runner.invoke(app, ["plan", "8", "60"])
        assert result.exit_code == 0
        assert "beyond the band" not in result.stdout


class TestTerm:
    def test_it_lays_out_the_nights(self, runner, seeded) -> None:
        result = runner.invoke(app, ["term", "2023-09-05", "2023-12-19"])
        assert result.exit_code == 0
        assert "Tuesdays" in result.stdout

    def test_another_night_can_be_asked_for(self, runner, seeded) -> None:
        result = runner.invoke(app, ["term", "2023-09-05", "2023-12-19", "-n", "3"])
        assert "Thursdays" in result.stdout

    def test_it_can_work_from_a_named_set(self, runner, seeded) -> None:
        result = runner.invoke(app, ["term", "2023-09-05", "2023-12-19", "-f", "the standard four"])
        assert result.exit_code == 0

    def test_a_set_nobody_names(self, runner, seeded) -> None:
        result = runner.invoke(app, ["term", "2023-09-05", "2023-12-19", "-f", "the weasel four"])
        assert result.exit_code != 0

    def test_more_than_a_term(self, runner, seeded) -> None:
        assert runner.invoke(app, ["term", "2023-01-01", "2025-01-01"]).exit_code != 0
