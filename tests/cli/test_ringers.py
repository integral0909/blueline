from blueline.cli.commands.common import EXIT_FOR
from blueline.cli.main import app
from blueline.service.results import Reason

CAMBRIDGE = "Cambridge Surprise Major"
PLAIN = "Plain Bob Major"
YORKSHIRE = "Yorkshire Surprise Major"


def a_band(runner):
    for name in ("Ann", "Bob", "Cara", "Dan", "Eve", "Finn"):
        runner.invoke(app, ["ringer", name, "-r", CAMBRIDGE, "-r", PLAIN])
    runner.invoke(app, ["ringer", "Gus", "-r", PLAIN, "-l", CAMBRIDGE])
    runner.invoke(app, ["ringer", "Hana", "-r", PLAIN, "-l", YORKSHIRE])


class TestAdding:
    def test_somebody_can_be_added(self, runner, library):
        result = runner.invoke(app, ["ringer", "Ann", "-r", CAMBRIDGE])
        assert result.exit_code == 0
        assert "1 methods" in result.stdout

    def test_it_mentions_what_they_are_learning(self, runner, library):
        result = runner.invoke(app, ["ringer", "Gus", "-l", CAMBRIDGE])
        assert "learning" in result.stdout

    def test_the_same_name_twice_exits_with_the_conflict_code(self, runner, library):
        runner.invoke(app, ["ringer", "Ann"])
        again = runner.invoke(app, ["ringer", "Ann"])
        assert again.exit_code == EXIT_FOR[Reason.ALREADY_EXISTS]

    def test_ringing_and_learning_the_same_method_exits_invalid(self, runner, library):
        result = runner.invoke(app, ["ringer", "Ann", "-r", CAMBRIDGE, "-l", CAMBRIDGE])
        assert result.exit_code == EXIT_FOR[Reason.INVALID]


class TestListing:
    def test_an_empty_tower_lists_nobody(self, runner, library):
        assert "0 ringers" in runner.invoke(app, ["ringers"]).stdout

    def test_it_lists_everybody(self, runner, library):
        a_band(runner)
        assert "8 ringers" in runner.invoke(app, ["ringers"]).stdout

    def test_it_shows_what_they_are_learning(self, runner, library):
        a_band(runner)
        assert "Cambridge" in runner.invoke(app, ["ringers"]).stdout


class TestLearnt:
    def test_it_moves_a_method_across(self, runner, library):
        a_band(runner)
        result = runner.invoke(app, ["learnt", "Gus", CAMBRIDGE])
        assert result.exit_code == 0
        assert "2 methods" in result.stdout

    def test_it_is_saved(self, runner, library):
        a_band(runner)
        runner.invoke(app, ["learnt", "Gus", CAMBRIDGE])
        assert "Gus" in runner.invoke(app, ["who-rings", CAMBRIDGE]).stdout

    def test_somebody_who_is_not_there_exits_not_found(self, runner, library):
        result = runner.invoke(app, ["learnt", "Nobody", CAMBRIDGE])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]


class TestRemoving:
    def test_somebody_can_be_removed(self, runner, library):
        a_band(runner)
        result = runner.invoke(app, ["unringer", "Hana"])
        assert result.exit_code == 0
        assert "removed Hana" in result.stdout

    def test_they_are_gone_afterwards(self, runner, library):
        a_band(runner)
        runner.invoke(app, ["unringer", "Hana"])
        assert "7 ringers" in runner.invoke(app, ["ringers"]).stdout

    def test_removing_somebody_who_is_not_there_exits_not_found(self, runner, library):
        result = runner.invoke(app, ["unringer", "Nobody"])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]


class TestWhoRings:
    def test_it_lists_who_can(self, runner, library):
        a_band(runner)
        result = runner.invoke(app, ["who-rings", CAMBRIDGE])
        assert "Ann" in result.stdout
        assert "Gus" not in result.stdout

    def test_a_method_nobody_rings_lists_nobody(self, runner, library):
        a_band(runner)
        result = runner.invoke(app, ["who-rings", YORKSHIRE])
        assert result.stdout.strip() == ""


class TestLearning:
    def test_it_groups_by_method(self, runner, library):
        a_band(runner)
        result = runner.invoke(app, ["learning"])
        assert f"{CAMBRIDGE}: Gus" in result.stdout

    def test_a_tower_learning_nothing_has_nothing(self, runner, library):
        runner.invoke(app, ["ringer", "Ann", "-r", PLAIN])
        assert runner.invoke(app, ["learning"]).stdout.strip() == ""


class TestBandCanRing:
    def test_it_says_what_they_can_get_through(self, runner, seeded):
        a_band(runner)
        result = runner.invoke(app, ["band-can-ring", "8"])
        assert PLAIN in result.stdout
        assert CAMBRIDGE not in result.stdout

    def test_once_the_learner_has_it_they_can(self, runner, seeded):
        a_band(runner)
        runner.invoke(app, ["learnt", "Gus", CAMBRIDGE])
        assert CAMBRIDGE in runner.invoke(app, ["band-can-ring", "8"]).stdout

    def test_a_band_too_small_exits_invalid(self, runner, seeded):
        runner.invoke(app, ["ringer", "Ann"])
        result = runner.invoke(app, ["band-can-ring", "8"])
        assert result.exit_code == EXIT_FOR[Reason.INVALID]
