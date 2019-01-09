"""The command groups have to stay apart and stay registered."""

from __future__ import annotations

from typing import List, Set

from click.testing import CliRunner

from blueline.cli.commands import (
    methods,
    performances,
    plans,
    ringers,
    touches,
    towers,
)
from blueline.cli.commands.common import EXIT_FOR
from blueline.cli.main import app
from blueline.service.results import Reason

GROUPS = {
    "methods": methods.app,
    "touches": touches.app,
    "performances": performances.app,
    "towers": towers.app,
    "plans": plans.app,
    "ringers": ringers.app,
}


def names(group) -> Set[str]:
    """The command names in a group, however it happens to hold them.

    A declare.Group keeps a list of built commands; the assembled click group
    at the top keeps a dict keyed by name.
    """
    if hasattr(group, "registered_commands"):
        return {command.name for command in group.registered_commands}
    return set(group.commands)


class TestSplit:
    def test_every_group_has_commands_in_it(self):
        for label, group in GROUPS.items():
            assert names(group), f"{label} is empty"

    def test_no_command_is_in_two_groups(self):
        seen: Set[str] = set()
        for group in GROUPS.values():
            assert not (names(group) & seen)
            seen |= names(group)

    def test_the_method_commands_are_together(self):
        assert {"analyse", "show", "line"} <= names(methods.app)

    def test_the_touch_commands_are_together(self):
        assert {"prove", "course", "search", "splice"} <= names(touches.app)

    def test_the_performance_commands_are_together(self):
        assert {"rang", "rung", "totals"} <= names(performances.app)

    def test_the_tower_commands_are_together(self):
        assert {"tower", "towers", "untower"} <= names(towers.app)

    def test_the_plan_commands_are_together(self):
        assert {"plan", "ringable"} <= names(plans.app)

    def test_the_ringer_commands_are_together(self):
        assert {"ringer", "ringers", "learnt", "learning"} <= names(ringers.app)


class TestRegistered:
    def test_every_command_reaches_the_application(self):
        registered = names(app)
        for group in GROUPS.values():
            assert names(group) <= registered

    def test_there_are_seventy_five_of_them(self):
        assert len(app.commands) == 75

    def test_they_are_all_at_the_top_level(self):
        # Nobody wants to type "blueline methods show".
        result = CliRunner().invoke(app, ["--help"])
        assert "show" in result.output
        assert "methods" not in result.output.split("Commands")[1].split("\n")[1]

    def test_the_help_lists_them(self):
        result = CliRunner().invoke(app, ["--help"])
        assert result.exit_code == 0
        for command in ("analyse", "prove", "rang", "totals"):
            assert command in result.output


class TestExitCodes:
    def test_every_reason_has_one(self):
        for reason in Reason:
            assert reason in EXIT_FOR

    def test_they_are_all_different(self):
        assert len(set(EXIT_FOR.values())) == len(EXIT_FOR)

    def test_none_of_them_mean_success(self):
        assert 0 not in EXIT_FOR.values()

    def test_the_groups_share_one_table(self):
        from blueline.cli import main

        assert main.EXIT_FOR is EXIT_FOR


class TestStores:
    def test_every_repository_shares_one_session(self, library):
        from blueline.cli.commands.common import stores

        opened = stores()
        assert opened.methods.session is opened.session
        assert opened.performances.session is opened.session
        assert opened.towers.session is opened.session

    def test_two_calls_give_two_sessions(self, library):
        from blueline.cli.commands.common import stores

        assert stores().session is not stores().session

    def test_committing_goes_through_the_session(self, library):
        from blueline.cli.commands.common import stores
        from tests.methods import PLAIN_BOB_MINOR

        opened = stores()
        opened.methods.add(PLAIN_BOB_MINOR)
        opened.commit()

        fresh = stores()
        assert fresh.methods.find("Plain Bob Minor") is not None

    def test_a_tower_and_a_performance_can_be_joined(self, library):
        # This is the thing that broke when each helper opened its own
        # session: the tower belonged to one and the performance to another.
        from blueline.cli.commands.common import stores
        from blueline.service import performances as perf_service
        from blueline.service import towers as tower_service

        opened = stores()
        tower_service.add(opened.towers, "St Andrew, Marchgate", 8, "23-1-14")
        result = perf_service.record(
            opened.performances,
            opened.methods,
            title="Cambridge Surprise Major",
            stage=8,
            length=5024,
            rang_on="2023-03-18",
            place="St Andrew, Marchgate",
            ringers=["Ann", "Bob", "Cara", "Dan", "Eve", "Finn", "Gus", "Hana"],
            conductor="Hana",
            towers=opened.towers,
        )
        assert result.ok
        assert result.unwrap().tower == "St Andrew, Marchgate"


class TestFlatNamespace:
    """Every command sits at the top level, so two groups can collide."""

    def names(self) -> List[str]:
        return sorted(app.commands)

    def test_no_two_commands_share_a_name(self) -> None:
        names = self.names()
        doubled = {name for name in names if names.count(name) > 1}
        assert not doubled, f"{sorted(doubled)} registered twice"

    def test_every_command_has_a_name(self) -> None:
        assert all(self.names())

    def test_no_name_has_an_underscore_in_it(self) -> None:
        # Typer would derive one from the function name. A command nobody can
        # guess the spelling of is a command nobody runs.
        assert not [name for name in self.names() if "_" in name]

    def test_every_group_is_mounted(self) -> None:
        from blueline.cli.main import GROUPS

        assert len(app.commands) == sum(len(group.registered_commands) for group in GROUPS)

    def test_no_group_is_mounted_twice(self) -> None:
        from blueline.cli.main import GROUPS

        assert len({id(group) for group in GROUPS}) == len(GROUPS)

    def test_the_transfer_commands_are_reachable(self) -> None:
        assert {"import", "export", "seed"} <= set(self.names())

    def test_the_method_commands_still_are(self) -> None:
        assert {"show", "line", "falseness"} <= set(self.names())
