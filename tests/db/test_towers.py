import pytest

from blueline.core.towers import Tower, Weight
from blueline.db.repository import TowerRepository, to_stored_tower, to_tower
from blueline.errors import LibraryError

MARCHGATE = Tower(place="St Andrew, Marchgate", bells=8, tenor=Weight(23, 1, 14))
ASHCOMBE = Tower(place="St Mary, Ashcombe", bells=6, tenor=Weight(8, 0, 0))
KELBROOK = Tower(place="All Saints, Kelbrook", bells=12, tenor=Weight(31, 2, 7))


@pytest.fixture()
def towers(session) -> TowerRepository:
    return TowerRepository(session)


@pytest.fixture()
def loaded(towers):
    for tower in (MARCHGATE, ASHCOMBE, KELBROOK):
        towers.add(tower)
    return towers


class TestConversion:
    def test_the_weight_flattens_to_pounds(self):
        assert to_stored_tower(MARCHGATE).tenor_pounds == Weight(23, 1, 14).total_pounds

    def test_it_goes_round_trip(self):
        assert to_tower(to_stored_tower(MARCHGATE)) == MARCHGATE

    def test_a_light_ring_goes_round_trip_too(self):
        assert to_tower(to_stored_tower(ASHCOMBE)).tenor == Weight(8, 0, 0)


class TestStoring:
    def test_one_can_be_stored(self, towers):
        towers.add(MARCHGATE)
        assert towers.count() == 1

    def test_it_can_be_fetched_back(self, towers):
        towers.add(MARCHGATE)
        assert towers.get("St Andrew, Marchgate").bells == 8

    def test_lookup_ignores_case_and_space(self, towers):
        towers.add(MARCHGATE)
        assert towers.get("  st andrew, marchgate ")

    def test_the_same_place_twice_is_refused(self, towers):
        towers.add(MARCHGATE)
        with pytest.raises(LibraryError, match="already"):
            towers.add(MARCHGATE)

    def test_find_gives_nothing_rather_than_raising(self, towers):
        assert towers.find("Nowhere") is None

    def test_get_names_what_was_asked_for(self, towers):
        with pytest.raises(LibraryError, match="Nowhere"):
            towers.get("Nowhere")

    def test_one_can_be_removed(self, towers, session):
        towers.add(MARCHGATE)
        towers.remove("St Andrew, Marchgate")
        session.flush()
        assert towers.count() == 0

    def test_removing_one_that_is_not_there_complains(self, towers):
        with pytest.raises(LibraryError):
            towers.remove("Nowhere")


class TestSearch:
    def test_the_heaviest_comes_first(self, loaded):
        assert [t.place for t in loaded.all()][0] == "All Saints, Kelbrook"

    def test_the_lightest_comes_last(self, loaded):
        assert [t.place for t in loaded.all()][-1] == "St Mary, Ashcombe"

    def test_it_finds_by_place(self, loaded):
        assert len(loaded.search(place="Marchgate")) == 1

    def test_a_place_matches_on_part_of_it(self, loaded):
        assert len(loaded.search(place="St ")) == 2

    def test_it_finds_by_number_of_bells(self, loaded):
        assert len(loaded.search(min_bells=8)) == 2

    def test_it_finds_by_an_upper_bound_too(self, loaded):
        assert len(loaded.search(max_bells=8)) == 2

    def test_it_finds_by_tenor_weight(self, loaded):
        heavy = loaded.search(min_tenor_pounds=Weight(20, 0, 0).total_pounds)
        assert len(heavy) == 2

    def test_filters_stack(self, loaded):
        found = loaded.search(min_bells=8, max_bells=8)
        assert [t.place for t in found] == ["St Andrew, Marchgate"]

    def test_a_search_matching_nothing_gives_nothing(self, loaded):
        assert loaded.search(place="Nowhere") == []

    def test_it_finds_towers_able_to_ring_a_stage(self, loaded):
        assert len(loaded.able_to_ring(8)) == 2
        assert len(loaded.able_to_ring(12)) == 1

    def test_an_empty_repository_finds_nothing(self, towers):
        assert towers.all() == []
        assert towers.able_to_ring(6) == []
