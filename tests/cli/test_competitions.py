"""Competitions from the command line."""

from __future__ import annotations

import pytest

from blueline.cli.commands.competitions import read_sheet
from blueline.cli.main import app

SHEET = """
# Marchgate District Striking, 6 May 2023
1 St Mary 12
2 All Saints 19  # method mistake in the third course
3 St Peter 34
"""


@pytest.fixture()
def sheet(tmp_path):
    path = tmp_path / "sheet.txt"
    path.write_text(SHEET)
    return path


@pytest.fixture()
def recording(tmp_path):
    times = " ".join(str(round(index * 0.2, 4)) for index in range(24))
    path = tmp_path / "recording.txt"
    path.write_text(f"St Mary: {times}\nAll Saints: {times}\n")
    return path


class TestReadingASheet:
    def test_it_reads_the_placings(self) -> None:
        entries = read_sheet(SHEET)
        assert [entry.position for entry in entries] == [1, 2, 3]

    def test_a_band_name_can_have_spaces(self) -> None:
        assert read_sheet(SHEET)[1].band == "All Saints"

    def test_the_faults_come_off_the_end(self) -> None:
        assert read_sheet(SHEET)[0].faults == 12

    def test_a_note_after_a_hash_is_kept(self) -> None:
        assert "method mistake" in read_sheet(SHEET)[1].note

    def test_a_short_line(self) -> None:
        with pytest.raises(Exception, match="wanted position"):
            read_sheet("1 StMary\n")

    def test_something_that_is_not_a_number(self) -> None:
        with pytest.raises(Exception, match="have to be numbers"):
            read_sheet("first St Mary twelve\n")

    def test_a_position_of_zero(self) -> None:
        with pytest.raises(Exception, match="starts at one"):
            read_sheet("0 St Mary 12\n")

    def test_an_empty_sheet(self) -> None:
        with pytest.raises(Exception, match="nobody on that sheet"):
            read_sheet("# nothing\n")


class TestRecording:
    def test_a_sheet_can_be_written_up(self, runner, library, sheet) -> None:
        result = runner.invoke(app, ["competition", str(sheet), "District", "2023-05-06", "6"])
        assert result.exit_code == 0
        assert "St Mary" in result.output

    def test_it_is_stored(self, runner, library, sheet) -> None:
        runner.invoke(app, ["competition", str(sheet), "District", "2023-05-06", "6"])
        result = runner.invoke(app, ["competitions"])
        assert "1 competitions" in result.output

    def test_the_same_one_twice_is_refused(self, runner, library, sheet) -> None:
        runner.invoke(app, ["competition", str(sheet), "District", "2023-05-06", "6"])
        result = runner.invoke(app, ["competition", str(sheet), "District", "2023-05-06", "6"])
        assert result.exit_code != 0

    def test_a_place_can_be_given(self, runner, library, sheet) -> None:
        result = runner.invoke(
            app,
            ["competition", str(sheet), "District", "2023-05-06", "6", "-p", "St Andrew"],
        )
        assert result.exit_code == 0


class TestJudging:
    def test_a_recording_is_marked_and_stored(self, runner, library, recording) -> None:
        result = runner.invoke(app, ["judged", str(recording), "District", "2023-05-06", "6"])
        assert result.exit_code == 0
        assert "St Mary" in result.output

    def test_it_shows_up_in_the_listing(self, runner, library, recording) -> None:
        runner.invoke(app, ["judged", str(recording), "District", "2023-05-06", "6"])
        assert "1 competitions" in runner.invoke(app, ["competitions"]).output


class TestListing:
    def load(self, runner, sheet):
        runner.invoke(app, ["competition", str(sheet), "District", "2022-05-07", "6"])
        runner.invoke(app, ["competition", str(sheet), "District", "2023-05-06", "6"])

    def test_nothing_stored(self, runner, library) -> None:
        assert "0 competitions" in runner.invoke(app, ["competitions"]).output

    def test_by_name(self, runner, library, sheet) -> None:
        self.load(runner, sheet)
        assert "2 competitions" in runner.invoke(app, ["competitions", "-n", "Dist"]).output

    def test_by_band(self, runner, library, sheet) -> None:
        self.load(runner, sheet)
        assert "2 competitions" in runner.invoke(app, ["competitions", "-b", "St Mary"]).output


class TestBand:
    def test_a_bands_record(self, runner, library, sheet) -> None:
        runner.invoke(app, ["competition", str(sheet), "District", "2022-05-07", "6"])
        runner.invoke(app, ["competition", str(sheet), "District", "2023-05-06", "6"])
        result = runner.invoke(app, ["band", "St Mary"])
        assert "St Mary" in result.output

    def test_a_band_nobody_has_seen(self, runner, library) -> None:
        result = runner.invoke(app, ["band", "St Swithin"])
        assert result.exit_code == 0
        assert "too few to say" in result.output
