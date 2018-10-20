"""Competition sheets."""

from __future__ import annotations

from typing import List

from datetime import date

import pytest

from blueline.core.competitions import (
    Competition,
    CompetitionError,
    Entry,
    improving,
    placings,
    progress,
)


def an_entry(band: str = "St Mary", position: int = 1, **over) -> Entry:
    fields = {"faults": 12, "percentage": 97.5, "drift": "even"}
    fields.update(over)
    return Entry(band=band, position=position, **fields)


HELD = date(2023, 5, 6)


def a_sheet(held_on: date = HELD, *entries: Entry, **over) -> Competition:
    fields = {
        "name": "Marchgate District Striking",
        "stage": 6,
        "place": "St Andrew, Marchgate",
    }
    fields.update(over)
    return Competition(held_on=held_on, entries=tuple(entries), **fields)


class TestEntry:
    def test_it_reads_as_a_placing(self) -> None:
        assert str(an_entry()) == "1. St Mary, 12 faults"

    def test_a_band_needs_a_name(self) -> None:
        with pytest.raises(CompetitionError, match="needs a name"):
            an_entry(band="  ")

    def test_a_position_starts_at_one(self) -> None:
        with pytest.raises(CompetitionError, match="starts at one"):
            an_entry(position=0)

    def test_faults_cannot_be_negative(self) -> None:
        with pytest.raises(CompetitionError, match="negative"):
            an_entry(faults=-1)


class TestCompetition:
    def test_it_counts_the_bands(self) -> None:
        sheet = a_sheet(date(2023, 5, 6), an_entry(), an_entry("All Saints", 2))
        assert sheet.bands == 2

    def test_it_needs_a_name(self) -> None:
        with pytest.raises(CompetitionError, match="needs a name"):
            a_sheet(name="   ")

    def test_it_needs_bells(self) -> None:
        with pytest.raises(CompetitionError, match="needs bells"):
            a_sheet(stage=0)

    def test_a_band_cannot_enter_twice(self) -> None:
        with pytest.raises(CompetitionError, match="cannot enter twice"):
            a_sheet(date(2023, 5, 6), an_entry(), an_entry(position=2))

    def test_entries_come_out_in_order(self) -> None:
        sheet = a_sheet(date(2023, 5, 6), an_entry("All Saints", 2), an_entry("St Mary", 1))
        assert [entry.band for entry in sheet.ordered()] == ["St Mary", "All Saints"]

    def test_bands_placed_equal_come_out_alphabetically(self) -> None:
        sheet = a_sheet(date(2023, 5, 6), an_entry("St Mary", 1), an_entry("All Saints", 1))
        assert sheet.ordered()[0].band == "All Saints"

    def test_the_winner(self) -> None:
        sheet = a_sheet(date(2023, 5, 6), an_entry("St Mary", 1), an_entry("All Saints", 2))
        assert sheet.winner() is not None
        assert sheet.winner().band == "St Mary"

    def test_a_tie_has_no_winner(self) -> None:
        sheet = a_sheet(date(2023, 5, 6), an_entry("St Mary", 1), an_entry("All Saints", 1))
        assert sheet.winner() is None

    def test_finding_a_band(self) -> None:
        sheet = a_sheet(date(2023, 5, 6), an_entry("St Mary", 1))
        assert sheet.find("  st mary  ") is not None

    def test_a_band_that_did_not_enter(self) -> None:
        assert a_sheet(date(2023, 5, 6), an_entry()).find("St Peter") is None

    def test_a_summary_names_the_winner(self) -> None:
        sheet = a_sheet(date(2023, 5, 6), an_entry("St Mary", 1), an_entry("All Saints", 2))
        assert "won by St Mary" in sheet.summary()

    def test_a_summary_of_a_tie(self) -> None:
        sheet = a_sheet(date(2023, 5, 6), an_entry("St Mary", 1), an_entry("All Saints", 1))
        assert "won by a tie" in sheet.summary()

    def test_a_summary_of_an_empty_sheet(self) -> None:
        assert "nobody entered" in a_sheet().summary()


class TestProgress:
    def sheets(self) -> List[Competition]:
        return [
            a_sheet(date(2021, 5, 1), an_entry("St Mary", 4), an_entry("All Saints", 1)),
            a_sheet(date(2022, 5, 7), an_entry("St Mary", 3)),
            a_sheet(date(2023, 5, 6), an_entry("St Mary", 2), an_entry("All Saints", 3)),
        ]

    def test_where_a_band_came(self) -> None:
        assert placings(self.sheets()[0], "St Mary") == 4

    def test_a_band_that_did_not_enter_has_no_placing(self) -> None:
        assert placings(self.sheets()[1], "All Saints") is None

    def test_progress_is_oldest_first(self) -> None:
        seen = progress(self.sheets(), "St Mary")
        assert [place for _, place in seen] == [4, 3, 2]

    def test_a_missed_year_is_simply_absent(self) -> None:
        assert len(progress(self.sheets(), "All Saints")) == 2

    def test_a_band_climbing_is_improving(self) -> None:
        assert improving(self.sheets(), "St Mary") is True

    def test_a_band_slipping_is_not(self) -> None:
        assert improving(self.sheets(), "All Saints") is False

    def test_one_entry_says_nothing(self) -> None:
        assert improving(self.sheets()[:1], "St Mary") is None

    def test_a_band_nobody_has_seen(self) -> None:
        assert improving(self.sheets(), "St Peter") is None
