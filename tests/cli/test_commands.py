"""The command groups have to stay apart and stay registered."""

from __future__ import annotations

from typing import Set

from typer.testing import CliRunner

from blueline.cli.commands import methods, performances, touches
from blueline.cli.commands.common import EXIT_FOR
from blueline.cli.main import app
from blueline.service.results import Reason

GROUPS = {"methods": methods.app, "touches": touches.app, "performances": performances.app}


def names(group) -> Set[str]:
    return {command.name or command.callback.__name__ for command in group.registered_commands}


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


class TestRegistered:
    def test_every_command_reaches_the_application(self):
        registered = names(app)
        for group in GROUPS.values():
            assert names(group) <= registered

    def test_there_are_eighteen_of_them(self):
        assert len(app.registered_commands) == 18

    def test_they_are_all_at_the_top_level(self):
        # Nobody wants to type "blueline methods show".
        result = CliRunner().invoke(app, ["--help"])
        assert "show" in result.stdout
        assert "methods" not in result.stdout.split("Commands")[1].split("\n")[1]

    def test_the_help_lists_them(self):
        result = CliRunner().invoke(app, ["--help"])
        assert result.exit_code == 0
        for command in ("analyse", "prove", "rang", "totals"):
            assert command in result.stdout


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
