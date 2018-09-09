from blueline.cli.commands.common import EXIT_FOR
from blueline.cli.main import app
from blueline.service.results import Reason


def load(runner):
    runner.invoke(app, ["tower", "St Andrew, Marchgate", "-b", "8", "-t", "23-1-14"])
    runner.invoke(app, ["tower", "St Mary, Ashcombe", "-b", "6", "-t", "8-0-0"])
    runner.invoke(app, ["tower", "All Saints, Kelbrook", "-b", "12", "-t", "31-2-7"])


class TestAdding:
    def test_one_can_be_added(self, runner, library):
        result = runner.invoke(app, ["tower", "St Andrew, Marchgate", "-b", "8", "-t", "23-1-14"])
        assert result.exit_code == 0
        assert "8 bells" in result.stdout

    def test_a_heavy_ring_says_so(self, runner, library):
        result = runner.invoke(app, ["tower", "St Andrew", "-b", "8", "-t", "23-1-14"])
        assert "a heavy ring" in result.stdout

    def test_a_light_one_does_not(self, runner, library):
        result = runner.invoke(app, ["tower", "St Mary", "-b", "6", "-t", "8-0-0"])
        assert "heavy" not in result.stdout

    def test_the_same_place_twice_exits_with_the_conflict_code(self, runner, library):
        runner.invoke(app, ["tower", "St Andrew", "-b", "8", "-t", "23-1-14"])
        again = runner.invoke(app, ["tower", "St Andrew", "-b", "8", "-t", "23-1-14"])
        assert again.exit_code == EXIT_FOR[Reason.ALREADY_EXISTS]

    def test_a_weight_it_cannot_read_exits_invalid(self, runner, library):
        result = runner.invoke(app, ["tower", "St Andrew", "-b", "8", "-t", "heavy"])
        assert result.exit_code == EXIT_FOR[Reason.INVALID]


class TestListing:
    def test_an_empty_store_lists_nothing(self, runner, library):
        assert "0 towers" in runner.invoke(app, ["towers"]).stdout

    def test_it_lists_what_is_there(self, runner, library):
        load(runner)
        assert "3 towers" in runner.invoke(app, ["towers"]).stdout

    def test_it_filters_by_place(self, runner, library):
        load(runner)
        assert "1 towers" in runner.invoke(app, ["towers", "-p", "Marchgate"]).stdout

    def test_it_filters_by_bells(self, runner, library):
        load(runner)
        assert "2 towers" in runner.invoke(app, ["towers", "--min-bells", "8"]).stdout

    def test_it_filters_by_tenor_weight(self, runner, library):
        load(runner)
        assert "2 towers" in runner.invoke(app, ["towers", "--min-tenor", "20-0-0"]).stdout

    def test_a_weight_it_cannot_read_exits_invalid(self, runner, library):
        load(runner)
        result = runner.invoke(app, ["towers", "--min-tenor", "heavy"])
        assert result.exit_code == EXIT_FOR[Reason.INVALID]


class TestRemoving:
    def test_one_can_be_removed(self, runner, library):
        load(runner)
        result = runner.invoke(app, ["untower", "St Mary, Ashcombe"])
        assert result.exit_code == 0
        assert "removed" in result.stdout

    def test_it_is_gone_afterwards(self, runner, library):
        load(runner)
        runner.invoke(app, ["untower", "St Mary, Ashcombe"])
        assert "2 towers" in runner.invoke(app, ["towers"]).stdout

    def test_removing_one_that_is_not_there_exits_not_found(self, runner, library):
        result = runner.invoke(app, ["untower", "Nowhere"])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]
