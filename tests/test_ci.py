"""The workflow and the local gate have to keep running the same thing."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "check.yml"
SCRIPT = ROOT / "scripts" / "check.sh"
STEPS = ("lint", "types", "tests")


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

    def test_it_says_what_python_the_package_needs(self, workflow):
        assert 'python_requires=">=3.11"' in (ROOT / "setup.py").read_text()

    def test_the_workflow_runs_the_python_the_package_asks_for(self, workflow):
        assert 'python-version: "3.11"' in workflow

    def test_it_installs_the_dev_extras(self, workflow):
        assert 'pip install -e ".[dev]"' in workflow


class TestSameToolsBothSides:
    @pytest.mark.parametrize("tool", ["flake8", "mypy", "pytest"])
    def test_each_tool_runs_in_both_places(self, workflow, script, tool):
        assert tool in workflow
        assert f"$PY/{tool}" in script

    @pytest.mark.parametrize("tool", ["flake8", "mypy", "pytest"])
    def test_each_tool_is_a_dev_extra(self, tool):
        assert f'"{tool}"' in (ROOT / "setup.py").read_text()

    def test_the_runtime_dependencies_have_a_floor(self):
        # A minimum rather than an exact pin. The versions this needs are
        # current, and holding a library at one release is how a project ends
        # up where this one was: years behind and unable to run anywhere.
        setup = (ROOT / "setup.py").read_text()
        for floor in ("SQLAlchemy>=", "alembic>=", "click>=", "structlog>="):
            assert floor in setup
