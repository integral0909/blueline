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
