"""A tower's report for the year."""

from __future__ import annotations

from typing import Optional

from datetime import date

import pytest

from blueline.core.competitions import Competition, Entry
from blueline.core.ringers import Ringer
from blueline.db.repositories import CollectionRepository, CompetitionRepository
from blueline.service.annual import FIRST_YEAR, report
from blueline.service.performances import record
from blueline.service.results import Reason

PLACE = "St Andrew, Marchgate"
EIGHT = ["Ann", "Bob", "Cara", "Dan", "Eve", "Finn", "Gus", "Hana"]


@pytest.fixture()
def competitions(loaded) -> CompetitionRepository:
    return CompetitionRepository(loaded.session)


@pytest.fixture()
def collections(loaded) -> CollectionRepository:
    return CollectionRepository(loaded.session)


@pytest.fixture()
def rung(performances, loaded):
    def add(length: int, when: str, title: str = "Cambridge Surprise Major") -> None:
        record(
            performances,
            loaded,
            title=title,
            stage=8,
            length=length,
            rang_on=when,
            place=PLACE,
            ringers=EIGHT,
            conductor="Hana",
        )

    add(5024, "2023-04-09")
    add(1280, "2023-11-12")
    add(1280, "2023-12-25", "Yorkshire Surprise Major")
    add(336, "2023-06-06")
    add(5056, "2022-04-17")
    return performances


def make(performances, ringers, competitions, collections, methods, **over):
    fields = {"year": 2023, "place": PLACE}
    fields.update(over)
    return report(performances, ringers, competitions, collections, methods, **fields)


class TestCounting:
    def test_it_counts_the_peals(self, rung, ringers, competitions, collections, loaded) -> None:
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert view.peals == 1

    def test_it_counts_the_quarters(self, rung, ringers, competitions, collections, loaded) -> None:
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert view.quarters == 2

    def test_anything_else_is_counted_apart(
        self, rung, ringers, competitions, collections, loaded
    ) -> None:
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert view.other == 1

    def test_last_year_is_left_out(self, rung, ringers, competitions, collections, loaded) -> None:
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert view.peals + view.quarters + view.other == 4

    def test_it_adds_the_changes_up(self, rung, ringers, competitions, collections, loaded) -> None:
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert view.changes == 5024 + 1280 + 1280 + 336

    def test_it_counts_the_methods_rung(
        self, rung, ringers, competitions, collections, loaded
    ) -> None:
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert view.repertoire == 2

    def test_a_quiet_year(self, performances, ringers, competitions, collections, loaded) -> None:
        view = make(performances, ringers, competitions, collections, loaded).unwrap()
        assert view.quiet
        assert "nothing rung" in view.summary()

    def test_a_summary_reads_as_a_report(
        self, rung, ringers, competitions, collections, loaded
    ) -> None:
        assert "peals" in make(rung, ringers, competitions, collections, loaded).unwrap().summary()


class TestLeaders:
    def test_it_names_the_busiest_ringers(
        self, rung, ringers, competitions, collections, loaded
    ) -> None:
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert view.top_ringers

    def test_the_leaderboard_can_be_cut_short(
        self, rung, ringers, competitions, collections, loaded
    ) -> None:
        view = make(rung, ringers, competitions, collections, loaded, top=2).unwrap()
        assert len(view.top_ringers) <= 2

    def test_it_names_the_methods_most_rung(
        self, rung, ringers, competitions, collections, loaded
    ) -> None:
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert view.top_methods[0][0]

    def test_a_leaderboard_of_nothing_is_refused(
        self, rung, ringers, competitions, collections, loaded
    ) -> None:
        result = make(rung, ringers, competitions, collections, loaded, top=0)
        assert result.failure.reason is Reason.INVALID


class TestOccasions:
    def test_it_notices_easter(self, rung, ringers, competitions, collections, loaded) -> None:
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert "Easter Sunday" in view.occasions_rung

    def test_it_notices_christmas(self, rung, ringers, competitions, collections, loaded) -> None:
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert "Christmas Day" in view.occasions_rung

    def test_a_day_nothing_special_happened_is_not_listed(
        self, rung, ringers, competitions, collections, loaded
    ) -> None:
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert "Ash Wednesday" not in view.occasions_rung


class TestCompetitions:
    def enter(self, competitions, position: Optional[int]) -> None:
        entries = [Entry(band="All Saints", position=1, faults=8, percentage=99.0)]
        if position is not None:
            entries.append(Entry(band=PLACE, position=position, faults=20, percentage=96.0))
        competitions.add(
            Competition(
                name="District Striking",
                held_on=date(2023, 5, 6),
                stage=8,
                entries=tuple(entries),
            )
        )

    def test_a_competition_the_tower_entered(
        self, rung, ringers, competitions, collections, loaded
    ) -> None:
        self.enter(competitions, 2)
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert view.competitions[0].entered
        assert view.competitions[0].position == 2

    def test_one_it_did_not(self, rung, ringers, competitions, collections, loaded) -> None:
        self.enter(competitions, None)
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert not view.competitions[0].entered

    def test_a_line_reads_as_a_placing(
        self, rung, ringers, competitions, collections, loaded
    ) -> None:
        self.enter(competitions, 2)
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert "2 of 2" in str(view.competitions[0])

    def test_a_line_for_one_it_missed(
        self, rung, ringers, competitions, collections, loaded
    ) -> None:
        self.enter(competitions, None)
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert "did not enter" in str(view.competitions[0])

    def test_another_year_is_left_out(
        self, rung, ringers, competitions, collections, loaded
    ) -> None:
        self.enter(competitions, 2)
        view = make(rung, ringers, competitions, collections, loaded, year=2022).unwrap()
        assert view.competitions == ()


class TestBand:
    def test_it_counts_the_band(self, rung, ringers, competitions, collections, loaded) -> None:
        ringers.add(Ringer(name="Ann", can_ring=frozenset(), learning=frozenset()))
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert view.ringers == 1

    def test_it_measures_the_band_against_a_set(
        self, rung, ringers, competitions, collections, loaded
    ) -> None:
        ringers.add(
            Ringer(
                name="Ann",
                can_ring=frozenset({"Cambridge Surprise Major"}),
                learning=frozenset(),
            )
        )
        view = make(rung, ringers, competitions, collections, loaded).unwrap()
        assert 0 < view.covers < 1

    def test_a_set_nobody_names_leaves_it_at_nothing(
        self, rung, ringers, competitions, collections, loaded
    ) -> None:
        view = make(
            rung, ringers, competitions, collections, loaded, against="the weasel four"
        ).unwrap()
        assert view.covers == 0.0


class TestRefusals:
    def test_a_year_before_anybody_rang(
        self, rung, ringers, competitions, collections, loaded
    ) -> None:
        result = make(rung, ringers, competitions, collections, loaded, year=1500)
        assert result.failure.reason is Reason.INVALID

    def test_the_first_year_is_early_enough_to_be_useless(self) -> None:
        assert FIRST_YEAR <= 1700

    def test_a_report_about_nowhere(self, rung, ringers, competitions, collections, loaded) -> None:
        result = make(rung, ringers, competitions, collections, loaded, place="   ")
        assert result.failure.reason is Reason.INVALID
