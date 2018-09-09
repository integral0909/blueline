import pytest

from blueline.db.repository import TowerRepository
from blueline.service import towers as service
from blueline.service.results import Reason


@pytest.fixture()
def towers(repository) -> TowerRepository:
    return TowerRepository(repository.session)


@pytest.fixture()
def loaded(towers):
    service.add(towers, "St Andrew, Marchgate", 8, "23-1-14")
    service.add(towers, "St Mary, Ashcombe", 6, "8-0-0")
    service.add(towers, "All Saints, Kelbrook", 12, "31-2-7")
    return towers


class TestMakeTower:
    def test_it_builds_one(self):
        tower = service.make_tower("St Andrew", 8, "23-1-14").unwrap()
        assert tower.bells == 8
        assert str(tower.tenor) == "23-1-14"

    def test_a_weight_it_cannot_read_is_invalid(self):
        assert service.make_tower("St Andrew", 8, "heavy").failure.reason is Reason.INVALID

    def test_a_nonsense_weight_is_invalid(self):
        assert not service.make_tower("St Andrew", 8, "23-9-0").ok

    def test_a_place_with_no_name_is_invalid(self):
        assert not service.make_tower("   ", 8, "23-1-14").ok

    def test_a_silly_number_of_bells_is_invalid(self):
        assert not service.make_tower("St Andrew", 2, "23-1-14").ok


class TestAdding:
    def test_one_can_be_added(self, towers):
        view = service.add(towers, "St Andrew, Marchgate", 8, "23-1-14").unwrap()
        assert view.bells == 8
        assert view.tenor == "23-1-14"

    def test_it_is_stored(self, towers):
        service.add(towers, "St Andrew, Marchgate", 8, "23-1-14")
        assert towers.count() == 1

    def test_the_same_place_twice_is_a_conflict(self, towers):
        service.add(towers, "St Andrew, Marchgate", 8, "23-1-14")
        again = service.add(towers, "St Andrew, Marchgate", 8, "23-1-14")
        assert again.failure.reason is Reason.ALREADY_EXISTS

    def test_a_bad_weight_is_refused_before_the_database(self, towers):
        service.add(towers, "St Andrew", 8, "heavy")
        assert towers.count() == 0


class TestView:
    def test_a_heavy_ring_says_so(self, loaded):
        view = service.fetch(loaded, "St Andrew, Marchgate").unwrap()
        assert view.is_heavy
        assert "a heavy ring" in view.summary()

    def test_a_light_one_does_not(self, loaded):
        view = service.fetch(loaded, "St Mary, Ashcombe").unwrap()
        assert not view.is_heavy
        assert "heavy" not in view.summary()

    def test_it_carries_the_weight_both_ways(self, loaded):
        view = service.fetch(loaded, "St Andrew, Marchgate").unwrap()
        assert view.tenor == "23-1-14"
        assert view.tenor_pounds == 23 * 112 + 28 + 14

    def test_it_says_the_highest_stage(self, loaded):
        assert service.fetch(loaded, "All Saints, Kelbrook").unwrap().rings_up_to == 12


class TestFetchAndRemove:
    def test_one_that_is_not_there_is_not_found(self, towers):
        assert service.fetch(towers, "Nowhere").failure.reason is Reason.NOT_FOUND

    def test_one_can_be_removed(self, loaded):
        assert service.remove(loaded, "St Mary, Ashcombe").ok
        assert service.fetch(loaded, "St Mary, Ashcombe").failure.reason is Reason.NOT_FOUND

    def test_removing_one_that_is_not_there_is_not_found(self, towers):
        assert service.remove(towers, "Nowhere").failure.reason is Reason.NOT_FOUND


class TestSearch:
    def test_the_heaviest_comes_first(self, loaded):
        found = service.search(loaded).unwrap()
        assert found[0].place == "All Saints, Kelbrook"

    def test_it_finds_by_place(self, loaded):
        assert len(service.search(loaded, place="Marchgate").unwrap()) == 1

    def test_it_finds_by_bells(self, loaded):
        assert len(service.search(loaded, min_bells=8).unwrap()) == 2

    def test_it_finds_by_tenor_weight(self, loaded):
        assert len(service.search(loaded, min_tenor="20-0-0").unwrap()) == 2

    def test_a_weight_it_cannot_read_is_invalid(self, loaded):
        assert service.search(loaded, min_tenor="heavy").failure.reason is Reason.INVALID

    def test_a_search_matching_nothing_succeeds_with_nothing(self, loaded):
        assert service.search(loaded, place="Nowhere").unwrap() == []


class TestCanRing:
    def test_a_ring_of_eight_rings_major(self, loaded):
        assert service.can_ring(loaded, "St Andrew, Marchgate", 8).unwrap()

    def test_it_does_not_ring_royal(self, loaded):
        assert not service.can_ring(loaded, "St Andrew, Marchgate", 10).unwrap()

    def test_a_tower_that_is_not_there_is_not_found(self, towers):
        assert service.can_ring(towers, "Nowhere", 8).failure.reason is Reason.NOT_FOUND
