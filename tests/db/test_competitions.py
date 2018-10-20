"""Competition sheets in the database."""

from __future__ import annotations

from datetime import date

import pytest

from blueline.core.competitions import Competition, Entry
from blueline.db.repository import CompetitionRepository, to_competition
from blueline.errors import LibraryError

HELD = date(2023, 5, 6)


@pytest.fixture()
def competitions(session) -> CompetitionRepository:
    return CompetitionRepository(session)


def an_entry(band: str = "St Mary", position: int = 1, **over) -> Entry:
    fields = {"faults": 12, "percentage": 97.5, "drift": "even"}
    fields.update(over)
    return Entry(band=band, position=position, **fields)


def a_sheet(held_on: date = HELD, *entries: Entry, **over) -> Competition:
    fields = {
        "name": "Marchgate District Striking",
        "stage": 6,
        "place": "St Andrew, Marchgate",
        "judge": "F Ahman",
    }
    fields.update(over)
    return Competition(held_on=held_on, entries=tuple(entries), **fields)


class TestStoring:
    def test_one_goes_in(self, competitions):
        competitions.add(a_sheet(HELD, an_entry()))
        assert competitions.count() == 1

    def test_its_entries_go_in_with_it(self, competitions):
        stored = competitions.add(a_sheet(HELD, an_entry(), an_entry("All Saints", 2)))
        assert len(stored.entries) == 2

    def test_the_same_one_twice_is_refused(self, competitions):
        competitions.add(a_sheet(HELD, an_entry()))
        with pytest.raises(LibraryError, match="already stored"):
            competitions.add(a_sheet(HELD, an_entry()))

    def test_the_same_one_next_year_is_fine(self, competitions):
        competitions.add(a_sheet(HELD, an_entry()))
        competitions.add(a_sheet(date(2024, 5, 4), an_entry()))
        assert competitions.count() == 2

    def test_it_reads_back_as_the_core_type(self, competitions):
        stored = competitions.add(a_sheet(HELD, an_entry(), an_entry("All Saints", 2)))
        sheet = to_competition(stored)
        assert sheet.bands == 2
        assert sheet.winner().band == "St Mary"

    def test_a_note_survives_the_round_trip(self, competitions):
        stored = competitions.add(a_sheet(HELD, an_entry(note="method mistake")))
        assert to_competition(stored).entries[0].note == "method mistake"

    def test_removing_one(self, competitions):
        stored = competitions.add(a_sheet(HELD, an_entry()))
        competitions.remove(stored.id)
        assert competitions.count() == 0

    def test_removing_one_that_is_not_there(self, competitions):
        with pytest.raises(LibraryError, match="no competition number"):
            competitions.remove(404)


class TestSearching:
    @pytest.fixture()
    def stocked(self, competitions):
        competitions.add(
            a_sheet(date(2022, 5, 7), an_entry("St Mary", 1), an_entry("All Saints", 2))
        )
        competitions.add(a_sheet(HELD, an_entry("All Saints", 1), an_entry("St Peter", 2)))
        competitions.add(
            a_sheet(
                date(2023, 6, 10),
                an_entry("St Mary", 1),
                name="County Final",
                place="St Nicholas, Ashwell",
                stage=8,
            )
        )
        return competitions

    def test_everything_comes_back_most_recent_first(self, stocked):
        held = [stored.held_on for stored in stocked.all()]
        assert held == sorted(held, reverse=True)

    def test_by_name(self, stocked):
        assert len(stocked.search(name="County")) == 1

    def test_by_place(self, stocked):
        assert len(stocked.search(place="Marchgate")) == 2

    def test_by_stage(self, stocked):
        assert len(stocked.search(stage=8)) == 1

    def test_by_band(self, stocked):
        assert len(stocked.search(band="St Mary")) == 2

    def test_a_band_nobody_has_seen(self, stocked):
        assert stocked.search(band="St Swithin") == []

    def test_two_things_at_once(self, stocked):
        assert len(stocked.search(band="St Mary", stage=6)) == 1

    def test_sheets_come_back_as_the_core_type(self, stocked):
        assert all(isinstance(sheet, Competition) for sheet in stocked.sheets())

    def test_a_band_gets_its_own_sheets(self, stocked):
        sheets = stocked.for_band("St Mary")
        assert len(sheets) == 2
        assert all(sheet.find("St Mary") is not None for sheet in sheets)

    def test_finding_one_by_name_and_date(self, stocked):
        assert stocked.find("marchgate district striking", HELD) is not None

    def test_finding_one_that_did_not_happen(self, stocked):
        assert stocked.find("Marchgate District Striking", date(2019, 5, 4)) is None
