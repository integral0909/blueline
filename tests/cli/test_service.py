"""Running the thing, and saying where it is pointed."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from blueline.cli.commands.service import DEFAULT_HOST, DEFAULT_PORT
from blueline.cli.main import app


@pytest.fixture()
def config(tmp_path):
    path = tmp_path / "blueline.toml"
    path.write_text('[blueline]\ndatabase_url = "sqlite:///vestry.db"\nrequest_limit = 12\n')
    return path


class TestWhere:
    def test_it_says_what_database(self, runner, config) -> None:
        result = runner.invoke(app, ["where", "-c", str(config)])
        assert result.exit_code == 0
        assert "vestry.db" in result.stdout

    def test_it_says_the_limit(self, runner, config) -> None:
        result = runner.invoke(app, ["where", "-c", str(config)])
        assert "12 per 60s" in result.stdout

    def test_without_a_file_it_says_the_defaults(self, runner, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["where"])
        assert result.exit_code == 0

    def test_a_file_that_cannot_be_read(self, runner, tmp_path) -> None:
        bad = tmp_path / "bad.toml"
        bad.write_text("[blueline]\nrequest_limmit = 12\n")
        result = runner.invoke(app, ["where", "-c", str(bad)])
        assert result.exit_code == 2

    def test_it_says_what_was_wrong_with_the_file(self, runner, tmp_path) -> None:
        bad = tmp_path / "bad.toml"
        bad.write_text("[blueline]\nrequest_limmit = 12\n")
        result = runner.invoke(app, ["where", "-c", str(bad)])
        assert "request_limmit" in result.output


class TestServe:
    def test_it_runs_the_application(self, runner, config) -> None:
        with patch("uvicorn.run") as run:
            result = runner.invoke(app, ["serve", "-c", str(config)])
        assert result.exit_code == 0
        assert run.called

    def test_it_listens_where_it_is_told(self, runner, config) -> None:
        with patch("uvicorn.run") as run:
            runner.invoke(app, ["serve", "-c", str(config), "--port", "9001"])
        assert run.call_args.kwargs["port"] == 9001

    def test_the_defaults_are_local(self, runner, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        with patch("uvicorn.run") as run:
            runner.invoke(app, ["serve"])
        assert run.call_args.kwargs["host"] == DEFAULT_HOST
        assert run.call_args.kwargs["port"] == DEFAULT_PORT

    def test_reloading_hands_over_an_import_path(self, runner, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        with patch("uvicorn.run") as run:
            runner.invoke(app, ["serve", "--reload"])
        assert run.call_args.args[0] == "blueline.api.app:app"

    def test_reloading_with_a_file_is_refused(self, runner, config) -> None:
        with patch("uvicorn.run") as run:
            result = runner.invoke(app, ["serve", "-c", str(config), "--reload"])
        assert result.exit_code == 2
        assert not run.called

    def test_a_file_that_cannot_be_read(self, runner, tmp_path) -> None:
        bad = tmp_path / "bad.toml"
        bad.write_text("nonsense = = =\n")
        with patch("uvicorn.run") as run:
            result = runner.invoke(app, ["serve", "-c", str(bad)])
        assert result.exit_code == 2
        assert not run.called
