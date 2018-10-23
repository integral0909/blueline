"""Recording competitions."""

from __future__ import annotations

from typing import List

from datetime import date

import pytest

from blueline.core.competitions import Entry
from blueline.db.repository import CompetitionRepository
from blueline.service.competitions import (
    band_progress,
    entries_from_times,
    fetch,
    judge_and_record,
    listing,
    record,
    remove,
)
from blueline.service.results import Reason

HELD = date(2023, 5, 6)


@pytest.fixture()
def competitions(session) -> CompetitionRepository:
    return CompetitionRepository(session)


def an_entry(band: str = "St Mary", position: int = 1, **over) -> Entry:
    fields = {"faults": 12, "percentage": 97.5, "drift": "even"}
    fields.update(over)
    return Entry(band=band, position=position, **fields)


def steady(blows: int, gap: float = 0.2) -> List[float]:
    return [round(index * gap, 4) for index in range(blows)]


def ragged(blows: int, at: int, error: float = 0.15) -> List[float]:
    return [
        round(time + (error if index > at else 0.0), 4) for index, time in enumerate(steady(blows))
    ]


class TestRecording:
    def test_a_sheet_goes_in(self, competitions):
        result = record(competitions, "District", HELD, 6, (an_entry(),))
        assert result.ok
        assert result.unwrap().bands == 1

    def test_the_winner_is_named(self, competitions):
        view = record(
            competitions, "District", HELD, 6, (an_entry(), an_entry("All Saints", 2))
        ).unwrap()
        assert view.winner == "St Mary"

    def test_a_tie_names_nobody(self, competitions):
        view = record(
            competitions, "District", HELD, 6, (an_entry(), an_entry("All Saints", 1))
        ).unwrap()
        assert view.winner == ""

    def test_entries_come_back_in_order(self, competitions):
        view = record(
            competitions, "District", HELD, 6, (an_entry("All Saints", 2), an_entry("St Mary", 1))
        ).unwrap()
        assert [entry.band for entry in view.entries] == ["St Mary", "All Saints"]

    def test_a_nameless_competition_is_refused(self, competitions):
        result = record(competitions, "   ", HELD, 6, (an_entry(),))
        assert result.failure.reason is Reason.INVALID

    def test_a_band_entering_twice_is_refused(self, competitions):
        result = record(competitions, "District", HELD, 6, (an_entry(), an_entry(position=2)))
        assert result.failure.reason is Reason.INVALID

    def test_the_same_one_twice_is_refused(self, competitions):
        record(competitions, "District", HELD, 6, (an_entry(),))
        result = record(competitions, "District", HELD, 6, (an_entry(),))
        assert result.failure.reason is Reason.ALREADY_EXISTS

    def test_a_summary_reads_as_a_sheet(self, competitions):
        view = record(competitions, "District", HELD, 6, (an_entry(),)).unwrap()
        assert view.summary() == "District, 2023-05-06, 1 bands"


class TestJudgingAndRecording:
    def test_the_marking_decides_the_order(self, competitions):
        attempts = {"St Mary": ragged(48, 10), "All Saints": steady(48)}
        view = judge_and_record(competitions, "District", HELD, 6, attempts).unwrap()
        assert view.entries[0].band == "All Saints"

    def test_positions_run_from_one(self, competitions):
        attempts = {"St Mary": ragged(48, 10), "All Saints": steady(48)}
        view = judge_and_record(competitions, "District", HELD, 6, attempts).unwrap()
        assert [entry.position for entry in view.entries] == [1, 2]

    def test_the_faults_are_carried_across(self, competitions):
        attempts = {"All Saints": steady(48)}
        view = judge_and_record(competitions, "District", HELD, 6, attempts).unwrap()
        assert view.entries[0].faults == 0

    def test_striking_that_cannot_be_judged(self, competitions):
        result = judge_and_record(competitions, "District", HELD, 6, {"St Mary": [0.0]})
        assert result.failure.reason is Reason.INVALID

    def test_no_bands_at_all(self, competitions):
        result = judge_and_record(competitions, "District", HELD, 6, {})
        assert result.failure.reason is Reason.INVALID

    def test_marking_alone_makes_entries(self):
        entries = entries_from_times({"All Saints": steady(24)}, 6).unwrap()
        assert entries[0].position == 1


class TestReadingBack:
    @pytest.fixture()
    def stocked(self, competitions):
        record(
            competitions,
            "District",
            date(2022, 5, 7),
            6,
            (an_entry("St Mary", 1), an_entry("All Saints", 2)),
        )
        record(
            competitions,
            "District",
            HELD,
            6,
            (an_entry("All Saints", 1), an_entry("St Mary", 3)),
        )
        record(competitions, "County Final", date(2023, 6, 10), 8, (an_entry("St Mary", 1),))
        return competitions

    def test_everything_is_listed(self, stocked):
        assert len(listing(stocked).unwrap()) == 3

    def test_listing_by_name(self, stocked):
        assert len(listing(stocked, name="County").unwrap()) == 1

    def test_listing_by_band(self, stocked):
        assert len(listing(stocked, band="All Saints").unwrap()) == 2

    def test_one_can_be_fetched(self, stocked):
        first = listing(stocked).unwrap()[0]
        assert fetch(stocked, first.id).unwrap().name == first.name

    def test_fetching_one_that_is_not_there(self, stocked):
        assert fetch(stocked, 404).failure.reason is Reason.NOT_FOUND

    def test_one_can_be_removed(self, stocked):
        first = listing(stocked).unwrap()[0]
        assert remove(stocked, first.id).ok
        assert len(listing(stocked).unwrap()) == 2

    def test_removing_one_that_is_not_there(self, stocked):
        assert remove(stocked, 404).failure.reason is Reason.NOT_FOUND


class TestProgress:
    @pytest.fixture()
    def stocked(self, competitions):
        record(competitions, "District", date(2021, 5, 1), 6, (an_entry("St Mary", 4),))
        record(competitions, "District", date(2022, 5, 7), 6, (an_entry("St Mary", 3),))
        record(competitions, "District", HELD, 6, (an_entry("St Mary", 2),))
        return competitions

    def test_it_lists_the_placings(self, stocked):
        view = band_progress(stocked, "St Mary").unwrap()
        assert [place for _, place in view.placings] == [4, 3, 2]

    def test_a_climbing_band_is_improving(self, stocked):
        assert band_progress(stocked, "St Mary").unwrap().improving is True

    def test_it_knows_the_best_placing(self, stocked):
        assert band_progress(stocked, "St Mary").unwrap().best == 2

    def test_a_band_nobody_has_seen(self, stocked):
        view = band_progress(stocked, "St Swithin").unwrap()
        assert view.entered == 0
        assert "has not entered" in view.summary()

    def test_a_summary_says_which_way(self, stocked):
        assert "improving" in band_progress(stocked, "St Mary").unwrap().summary()

    def test_a_nameless_band(self, stocked):
        assert band_progress(stocked, "  ").failure.reason is Reason.INVALID
