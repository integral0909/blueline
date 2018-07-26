"""The workflow and the local gate have to keep running the same thing."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "check.yml"
SCRIPT = ROOT / "scripts" / "check.sh"
STEPS = ("format", "lint", "types", "tests")


@pytest.fixture(scope="module")
def workflow() -> str:
    return WORKFLOW.read_text()


@pytest.fixture(scope="module")
def script() -> str:
    return SCRIPT.read_text()


class TestWorkflow:
    def test_it_is_there(self):
        assert WORKFLOW.exists()

    def test_it_runs_on_pushes_and_pull_requests(self, workflow):
        assert "push:" in workflow
        assert "pull_request:" in workflow

    def test_it_runs_every_step(self, workflow):
        for step in STEPS:
            assert f"name: {step}" in workflow

    def test_the_steps_are_in_the_same_order_as_the_script(self, workflow, script):
        in_workflow = [workflow.index(f"name: {step}") for step in STEPS]
        in_script = [script.index(f"run {step} ") for step in STEPS]
        assert in_workflow == sorted(in_workflow)
        assert in_script == sorted(in_script)

    def test_it_uses_the_python_the_project_needs(self, workflow):
        pyproject = (ROOT / "pyproject.toml").read_text()
        assert 'requires-python = ">=3.11"' in pyproject
        assert 'python-version: "3.11"' in workflow

    def test_it_installs_the_dev_extras(self, workflow):
        assert 'pip install -e ".[dev]"' in workflow


class TestSameToolsBothSides:
    @pytest.mark.parametrize("tool", ["black", "ruff", "mypy", "pytest"])
    def test_each_tool_runs_in_both_places(self, workflow, script, tool):
        assert tool in workflow
        assert f"$PY/{tool}" in script

    @pytest.mark.parametrize("tool", ["black", "ruff", "mypy", "pytest"])
    def test_each_tool_is_pinned(self, tool):
        assert f'"{tool}==' in (ROOT / "pyproject.toml").read_text()

    def test_the_workflow_checks_formatting_rather_than_changing_it(self, workflow):
        assert "black --check" in workflow
