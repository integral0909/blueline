from datetime import date

import pytest

from blueline.core.bands import band_of
from blueline.core.performance import Performance
from blueline.db.repository import (
    MethodRepository,
    PerformanceRepository,
    to_performance,
    to_stored_performance,
)
from blueline.errors import LibraryError
from tests.methods import CAMBRIDGE_MAJOR

BAND = band_of(["Ann", "Bob", "Cara", "Dan", "Eve", "Finn", "Gus", "Hana"], conductor="Hana")


def a_performance(**over) -> Performance:
    fields = {
        "band": BAND,
        "title": "Cambridge Surprise Major",
        "stage": 8,
        "length": 5024,
        "rang_on": date(2023, 3, 18),
        "place": "St Andrew, Marchgate",
        "composer": "F Ahman",
    }
    fields.update(over)
    return Performance(**fields)


@pytest.fixture()
def performances(session) -> PerformanceRepository:
    return PerformanceRepository(session)


class TestConversion:
    def test_the_band_flattens_to_lines(self):
        stored = to_stored_performance(a_performance())
        assert stored.ringers.splitlines()[0] == "Ann"

    def test_the_conductor_is_kept(self):
        assert to_stored_performance(a_performance()).conductor == 8

    def test_it_goes_round_trip(self):
        back = to_performance(to_stored_performance(a_performance()))
        assert back.band.ringers == BAND.ringers
        assert back.band.conducted_by == "Hana"
        assert back.length == 5024
        assert back.rang_on == date(2023, 3, 18)


class TestStoring:
    def test_one_can_be_stored(self, performances):
        performances.add(a_performance())
        assert performances.count() == 1

    def test_it_gets_an_id(self, performances):
        assert performances.add(a_performance()).id is not None

    def test_it_can_be_fetched_back(self, performances):
        stored = performances.add(a_performance())
        assert performances.get(stored.id).length == 5024

    def test_one_that_is_not_there_complains(self, performances):
        with pytest.raises(LibraryError, match="no performance"):
            performances.get(999)

    def test_it_can_hang_off_a_method(self, session, performances):
        method = MethodRepository(session).add(CAMBRIDGE_MAJOR)
        stored = performances.add(a_performance(), method=method)
        assert stored.method.title == "Cambridge Surprise Major"

    def test_an_empty_repository_holds_nothing(self, performances):
        assert performances.count() == 0
        assert performances.all() == []
        assert performances.places() == []


class TestSearch:
    @pytest.fixture()
    def loaded(self, performances):
        performances.add(a_performance())
        performances.add(
            a_performance(
                title="Grandsire Triples",
                stage=7,
                length=5040,
                rang_on=date(2023, 4, 2),
                place="St Mary, Ashcombe",
                band=band_of(["Ivy", "Jed", "Kit", "Lex", "Mo", "Nell", "Opal", "Pia"]),
            )
        )
        performances.add(
            a_performance(length=1250, rang_on=date(2023, 2, 1), title="Yorkshire Surprise Major")
        )
        return performances

    def test_the_most_recent_comes_first(self, loaded):
        assert [p.rang_on for p in loaded.all()] == [
            date(2023, 4, 2),
            date(2023, 3, 18),
            date(2023, 2, 1),
        ]

    def test_it_finds_by_place(self, loaded):
        assert len(loaded.search(place="Ashcombe")) == 1

    def test_a_place_matches_on_part_of_it(self, loaded):
        assert len(loaded.search(place="St ")) == 3

    def test_it_finds_by_title(self, loaded):
        assert len(loaded.search(title="Cambridge")) == 1

    def test_it_finds_by_stage(self, loaded):
        assert len(loaded.search(stage=7)) == 1

    def test_it_finds_by_length(self, loaded):
        assert len(loaded.search(min_length=5000)) == 2

    def test_it_finds_by_ringer(self, loaded):
        found = loaded.search(ringer="Hana")
        assert len(found) == 2

    def test_a_ringer_who_rang_nothing_finds_nothing(self, loaded):
        assert loaded.search(ringer="Nobody") == []

    def test_filters_stack(self, loaded):
        assert len(loaded.search(stage=8, min_length=5000)) == 1

    def test_it_lists_the_places(self, loaded):
        assert loaded.places() == ["St Andrew, Marchgate", "St Mary, Ashcombe"]

    def test_it_picks_out_the_peals(self, loaded):
        peals = loaded.peals()
        assert len(peals) == 2
        assert all(to_performance(p).is_peal for p in peals)

    def test_a_quarter_is_not_a_peal(self, loaded):
        assert 1250 not in [p.length for p in loaded.peals()]
