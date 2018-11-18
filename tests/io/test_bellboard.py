"""Writing a performance up the way it gets submitted."""

from __future__ import annotations

from datetime import date

import pytest

from blueline.core.bands import Band
from blueline.core.performance import Performance
from blueline.io.bellboard import BellboardError, read, write

EIGHT = ("Ann", "Bob", "Cara", "Dan", "Eve", "Finn", "Gus", "Hana")


def a_performance(**over) -> Performance:
    fields = {
        "band": Band(ringers=EIGHT, conductor=8),
        "title": "Cambridge Surprise Major",
        "stage": 8,
        "length": 5024,
        "rang_on": date(2023, 3, 18),
        "place": "St Andrew, Marchgate",
        "composer": "F Ahman",
    }
    fields.update(over)
    return Performance(**fields)


class TestWriting:
    def test_the_place_comes_first(self) -> None:
        assert write(a_performance()).lines[0] == "St Andrew, Marchgate"

    def test_the_date_reads_as_a_report_writes_it(self) -> None:
        assert "18 March 2023" in write(a_performance()).lines[1]

    def test_the_day_is_named(self) -> None:
        assert write(a_performance()).lines[1].startswith("Saturday")

    def test_the_length_and_method_go_together(self) -> None:
        assert "5024 Cambridge Surprise Major" in str(write(a_performance()))

    def test_the_composer_is_credited(self) -> None:
        assert "Composed by F Ahman" in str(write(a_performance()))

    def test_no_composer_is_left_out(self) -> None:
        assert "Composed by" not in str(write(a_performance(composer=None)))

    def test_the_band_is_one_a_line(self) -> None:
        text = str(write(a_performance()))
        assert "1 Ann" in text
        assert "8 Hana (C)" in text

    def test_only_the_conductor_is_marked(self) -> None:
        assert str(write(a_performance())).count("(C)") == 1

    def test_everybody_is_there(self) -> None:
        text = str(write(a_performance()))
        assert all(name in text for name in EIGHT)


class TestReading:
    def test_a_report_reads_back(self) -> None:
        original = a_performance()
        again = read(str(write(original)), stage=8)
        assert again.title == original.title
        assert again.length == original.length

    def test_the_band_reads_back(self) -> None:
        again = read(str(write(a_performance())), stage=8)
        assert again.band.ringers == EIGHT

    def test_the_conductor_reads_back(self) -> None:
        assert read(str(write(a_performance())), stage=8).band.conductor == 8

    def test_the_composer_reads_back(self) -> None:
        assert read(str(write(a_performance())), stage=8).composer == "F Ahman"

    def test_the_date_reads_back(self) -> None:
        assert read(str(write(a_performance())), stage=8).rang_on == date(2023, 3, 18)

    def test_a_length_with_a_comma_in_it(self) -> None:
        text = str(write(a_performance())).replace("5024", "5,024")
        assert read(text, stage=8).length == 5024

    def test_a_plain_date_is_read_too(self) -> None:
        text = str(write(a_performance())).replace("Saturday, 18 March 2023", "2023-03-18")
        assert read(text, stage=8).rang_on == date(2023, 3, 18)

    def test_treble_and_tenor_by_name(self) -> None:
        text = str(write(a_performance()))
        text = text.replace("1 Ann", "Treble Ann").replace("8 Hana", "Tenor Hana")
        assert read(text, stage=8).band.ringers == EIGHT

    def test_conductor_written_out_in_full(self) -> None:
        text = str(write(a_performance())).replace("(C)", "(conductor)")
        assert read(text, stage=8).band.conductor == 8


class TestRefusing:
    def test_a_report_that_is_too_short(self) -> None:
        with pytest.raises(BellboardError, match="needs a place"):
            read("St Andrew\n2023-03-18\n", stage=8)

    def test_a_date_it_cannot_read(self) -> None:
        text = str(write(a_performance())).replace("Saturday, 18 March 2023", "last Tuesday")
        with pytest.raises(BellboardError, match="not a date"):
            read(text, stage=8)

    def test_a_length_that_is_not_a_number(self) -> None:
        text = str(write(a_performance())).replace("5024 Cambridge", "lots of Cambridge")
        with pytest.raises(BellboardError, match="not a length"):
            read(text, stage=8)

    def test_a_line_that_is_not_a_band_line(self) -> None:
        text = str(write(a_performance())) + "\nrung half muffled"
        with pytest.raises(BellboardError, match="not a band line"):
            read(text, stage=8)

    def test_a_bell_given_twice(self) -> None:
        text = str(write(a_performance())).replace("2 Bob", "1 Bob")
        with pytest.raises(BellboardError, match="given twice"):
            read(text, stage=8)

    def test_a_bell_nobody_is_on(self) -> None:
        text = "\n".join(str(write(a_performance())).splitlines()[:-1])
        with pytest.raises(BellboardError, match="nobody is on bell 8"):
            read(text, stage=8)

    def test_the_stage_is_taken_rather_than_counted(self) -> None:
        # Counting the band would turn a report with a missing line into a
        # peal at a smaller stage rather than into an error.
        text = "\n".join(str(write(a_performance())).splitlines()[:-1])
        with pytest.raises(BellboardError):
            read(text, stage=8)
