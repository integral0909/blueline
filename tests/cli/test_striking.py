"""Judging striking from the command line."""

from __future__ import annotations

from typing import List

import pytest
from click.testing import CliRunner

from blueline.cli.commands.striking import read_attempts, read_times
from blueline.cli.main import app

runner = CliRunner()


def steady(blows: int, gap: float = 0.2) -> List[float]:
    return [round(index * gap, 4) for index in range(blows)]


def as_lines(times: List[float]) -> str:
    return "\n".join(str(time) for time in times) + "\n"


@pytest.fixture()
def attempt(tmp_path):
    path = tmp_path / "st-mary.txt"
    path.write_text(as_lines(steady(48)))
    return path


class TestReadingTimes:
    def test_one_a_line(self) -> None:
        assert read_times("0.0\n0.2\n0.4\n") == [0.0, 0.2, 0.4]

    def test_several_to_a_line(self) -> None:
        assert read_times("0.0 0.2 0.4") == [0.0, 0.2, 0.4]

    def test_blank_lines_are_skipped(self) -> None:
        assert read_times("0.0\n\n0.2\n") == [0.0, 0.2]

    def test_comments_are_skipped(self) -> None:
        assert read_times("# recorded at St Mary\n0.0\n0.2 # late\n") == [0.0, 0.2]

    def test_something_that_is_not_a_time(self) -> None:
        with pytest.raises(Exception, match="not a time"):
            read_times("0.0\nabout half past\n")


class TestReadingAttempts:
    def test_a_band_and_its_times(self) -> None:
        assert read_attempts("St Mary: 0.0 0.2 0.4") == {"St Mary": [0.0, 0.2, 0.4]}

    def test_times_run_on_over_lines(self) -> None:
        text = "St Mary:\n0.0\n0.2\nAll Saints:\n0.0\n0.4\n"
        assert read_attempts(text) == {"St Mary": [0.0, 0.2], "All Saints": [0.0, 0.4]}

    def test_two_bands_on_one_line_each(self) -> None:
        text = "St Mary: 0.0 0.2\nAll Saints: 0.0 0.4\n"
        assert list(read_attempts(text)) == ["St Mary", "All Saints"]

    def test_times_before_a_band_is_named(self) -> None:
        with pytest.raises(Exception, match="before any band"):
            read_attempts("0.0 0.2\n")

    def test_a_nameless_band(self) -> None:
        with pytest.raises(Exception, match="needs a name"):
            read_attempts(": 0.0 0.2\n")

    def test_an_empty_file(self) -> None:
        with pytest.raises(Exception, match="no bands"):
            read_attempts("# nothing here\n")


class TestStrike:
    def test_it_judges_a_file(self, attempt) -> None:
        result = runner.invoke(app, ["strike", str(attempt), "6"])
        assert result.exit_code == 0
        assert "0" in result.output

    def test_the_band_is_the_filename_by_default(self, attempt) -> None:
        result = runner.invoke(app, ["strike", str(attempt), "6"])
        assert "st-mary" in result.output

    def test_the_band_can_be_named(self, attempt) -> None:
        result = runner.invoke(app, ["strike", str(attempt), "6", "--band", "Ancient"])
        assert "Ancient" in result.output

    def test_a_missing_file(self, tmp_path) -> None:
        result = runner.invoke(app, ["strike", str(tmp_path / "gone.txt"), "6"])
        assert result.exit_code != 0

    def test_too_few_blows(self, tmp_path) -> None:
        path = tmp_path / "one.txt"
        path.write_text("0.0\n")
        result = runner.invoke(app, ["strike", str(path), "6"])
        assert result.exit_code != 0


class TestCompete:
    @pytest.fixture()
    def competition(self, tmp_path):
        path = tmp_path / "final.txt"
        path.write_text(
            "St Mary: " + " ".join(str(time) for time in steady(24)) + "\n"
            "All Saints: " + " ".join(str(time) for time in steady(24)) + "\n"
        )
        return path

    def test_it_judges_the_lot(self, competition) -> None:
        result = runner.invoke(app, ["compete", str(competition), "6"])
        assert result.exit_code == 0
        assert "2 bands" in result.output

    def test_both_bands_appear(self, competition) -> None:
        result = runner.invoke(app, ["compete", str(competition), "6"])
        assert "St Mary" in result.output

    def test_a_file_with_no_bands(self, tmp_path) -> None:
        path = tmp_path / "empty.txt"
        path.write_text("\n")
        result = runner.invoke(app, ["compete", str(path), "6"])
        assert result.exit_code != 0
