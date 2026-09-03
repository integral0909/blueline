"""The gate runner has to keep agreeing with what the project actually runs."""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check.sh"
STEPS = ("lint", "types", "tests")


@pytest.fixture(scope="module")
def source() -> str:
    return SCRIPT.read_text()


class TestScript:
    def test_it_is_there(self):
        assert SCRIPT.exists()

    def test_it_can_be_run(self):
        assert SCRIPT.stat().st_mode & stat.S_IXUSR

    def test_it_runs_every_step(self, source):
        for step in STEPS:
            assert f"run {step} " in source

    def test_the_quick_checks_come_first(self, source):
        order = [source.index(f"run {step} ") for step in STEPS]
        assert order == sorted(order)

    def test_it_stops_at_the_first_failure(self, source):
        assert "exit 1" in source

    def test_it_uses_the_tools_in_the_virtualenv(self, source):
        assert "PY=.venvnow/bin" in source
        assert "$PY/pytest" in source


class TestToolsMatchTheExtras:
    def test_every_tool_the_script_runs_is_a_dev_dependency(self, source):
        setup = (ROOT / "setup.py").read_text()
        for tool in ("flake8", "mypy", "pytest"):
            assert f"$PY/{tool}" in source
            assert f'"{tool}"' in setup
