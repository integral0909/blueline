"""Performances as reports, from the command line."""

from __future__ import annotations

import pytest

from blueline.cli.main import app

EIGHT = ["Ann", "Bob", "Cara", "Dan", "Eve", "Finn", "Gus", "Hana"]


@pytest.fixture()
def recorded(runner, seeded):
    runner.invoke(
        app,
        [
            "rang",
            "Cambridge Surprise Major",
            *sum((["-r", name] for name in EIGHT), []),
            "-s",
            "8",
            "-l",
            "5024",
            "--on",
            "2023-03-18",
            "-p",
            "St Andrew, Marchgate",
            "-c",
            "Hana",
        ],
    )
    return runner


class TestReport:
    def test_it_writes_one_up(self, recorded) -> None:
        result = recorded.invoke(app, ["report", "1"])
        assert result.exit_code == 0
        assert "St Andrew, Marchgate" in result.stdout

    def test_the_conductor_is_marked(self, recorded) -> None:
        assert "Hana (C)" in recorded.invoke(app, ["report", "1"]).stdout

    def test_one_that_is_not_there(self, recorded) -> None:
        assert recorded.invoke(app, ["report", "404"]).exit_code != 0


class TestPaste:
    def test_a_report_can_be_filed(self, recorded, tmp_path) -> None:
        text = recorded.invoke(app, ["report", "1"]).stdout
        path = tmp_path / "report.txt"
        path.write_text(text)
        result = recorded.invoke(app, ["paste", str(path), "8"])
        assert result.exit_code == 0

    def test_a_report_it_cannot_read(self, recorded, tmp_path) -> None:
        path = tmp_path / "report.txt"
        path.write_text("a lovely evening\n")
        assert recorded.invoke(app, ["paste", str(path), "8"]).exit_code != 0

    def test_a_missing_file(self, recorded, tmp_path) -> None:
        assert recorded.invoke(app, ["paste", str(tmp_path / "gone.txt"), "8"]).exit_code != 0
