import pytest

from blueline.db.repositories import TowerRepository
from blueline.service import plans as service
from blueline.service import towers as tower_service
from blueline.service.results import Reason


@pytest.fixture()
def towers(repository) -> TowerRepository:
    store = TowerRepository(repository.session)
    tower_service.add(store, "St Andrew, Marchgate", 8, "23-1-14")
    tower_service.add(store, "St Mary, Ashcombe", 6, "8-0-0")
    return store


class TestPlan:
    def test_it_fills_the_time(self, loaded):
        view = service.plan(loaded, ringers=8, minutes=60).unwrap()
        assert view.used_minutes <= 60

    def test_it_says_what_is_spare(self, loaded):
        view = service.plan(loaded, ringers=8, minutes=60).unwrap()
        assert view.spare_minutes == 60 - view.used_minutes

    def test_it_names_what_to_ring(self, loaded):
        view = service.plan(loaded, ringers=8, minutes=60).unwrap()
        assert view.items
        assert all("of" in item for item in view.items)

    def test_it_only_picks_what_the_band_can_ring(self, loaded):
        view = service.plan(loaded, ringers=6, minutes=60).unwrap()
        assert all(title.endswith((" 5", " 6")) for title in view.titles)

    def test_it_totals_the_changes(self, loaded):
        view = service.plan(loaded, ringers=8, minutes=60).unwrap()
        assert view.changes > 0

    def test_a_practice_of_no_time_is_invalid(self, loaded):
        assert service.plan(loaded, ringers=8, minutes=0).failure.reason is Reason.INVALID

    def test_a_band_too_small_is_invalid(self, loaded):
        assert service.plan(loaded, ringers=2, minutes=60).failure.reason is Reason.INVALID

    def test_a_speed_of_nothing_is_invalid(self, loaded):
        assert service.plan(loaded, ringers=8, minutes=60, speed=0).failure.reason is Reason.INVALID

    def test_an_empty_library_plans_nothing(self, repository):
        view = service.plan(repository, ringers=8, minutes=60).unwrap()
        assert view.items == ()
        assert "nothing this band can ring" in view.summary


class TestAtATower:
    def test_the_tower_caps_the_band(self, loaded, towers):
        # Eight people in a ring of six are still ringing minor.
        view = service.plan(
            loaded, ringers=8, minutes=60, towers=towers, place="St Mary, Ashcombe"
        ).unwrap()
        assert view.ringers == 6
        assert all(title.endswith((" 5", " 6")) for title in view.titles)

    def test_a_big_enough_tower_does_not_cap_it(self, loaded, towers):
        view = service.plan(
            loaded, ringers=8, minutes=60, towers=towers, place="St Andrew, Marchgate"
        ).unwrap()
        assert view.ringers == 8

    def test_a_tower_that_is_not_there_is_not_found(self, loaded, towers):
        result = service.plan(loaded, ringers=8, minutes=60, towers=towers, place="Nowhere")
        assert result.failure.reason is Reason.NOT_FOUND

    def test_naming_a_tower_with_none_stored_is_invalid(self, loaded):
        result = service.plan(loaded, ringers=8, minutes=60, place="Anywhere")
        assert result.failure.reason is Reason.INVALID


class TestWhatCanBeRung:
    def test_it_lists_what_a_band_could_ring(self, loaded):
        found = service.what_can_be_rung(loaded, 8).unwrap()
        assert all(title.endswith((" 7", " 8")) for title in found)

    def test_it_comes_back_sorted(self, loaded):
        found = service.what_can_be_rung(loaded, 8).unwrap()
        assert found == sorted(found)

    def test_a_band_too_small_is_invalid(self, loaded):
        assert service.what_can_be_rung(loaded, 2).failure.reason is Reason.INVALID

    def test_a_band_bigger_than_anything_stored_gets_nothing(self, loaded):
        assert service.what_can_be_rung(loaded, 16).unwrap() == []


class TestByWhatTheBandCanRing:
    def _band(self, repository):
        from blueline.db.repositories import RingerRepository
        from blueline.service import ringers as ringer_service

        store = RingerRepository(repository.session)
        for name in ("Ann", "Bob", "Cara", "Dan", "Eve", "Finn"):
            ringer_service.add(store, name, ["Plain Bob Major", "Cambridge Surprise Major"])
        ringer_service.add(store, "Gus", ["Plain Bob Major"], ["Cambridge Surprise Major"])
        ringer_service.add(store, "Hana", ["Plain Bob Major"])
        return store

    def test_it_only_picks_what_the_band_can_get_through(self, loaded, repository):
        band = self._band(repository)
        view = service.plan(loaded, ringers=8, minutes=60, band=band).unwrap()
        assert view.titles == ("Plain 8",)

    def test_it_says_what_was_left_out(self, loaded, repository):
        band = self._band(repository)
        view = service.plan(loaded, ringers=8, minutes=60, band=band).unwrap()
        assert "Cambridge Surprise Major" in view.beyond_the_band

    def test_once_the_learner_has_it_the_method_comes_in(self, loaded, repository):
        from blueline.service import ringers as ringer_service

        band = self._band(repository)
        ringer_service.learnt(band, "Gus", "Cambridge Surprise Major")
        ringer_service.learnt(band, "Hana", "Cambridge Surprise Major")
        view = service.plan(loaded, ringers=8, minutes=60, band=band).unwrap()
        assert "Cambridge 8" in view.titles
        assert "Cambridge Surprise Major" not in view.beyond_the_band

    def test_without_a_band_nothing_is_filtered(self, loaded):
        view = service.plan(loaded, ringers=8, minutes=60).unwrap()
        assert view.beyond_the_band == ()
        assert len(view.titles) > 1

    def test_an_empty_band_is_ignored_rather_than_ruling_everything_out(self, loaded, repository):
        from blueline.db.repositories import RingerRepository

        empty = RingerRepository(repository.session)
        view = service.plan(loaded, ringers=8, minutes=60, band=empty).unwrap()
        assert view.titles

    def test_it_still_honours_the_time(self, loaded, repository):
        band = self._band(repository)
        view = service.plan(loaded, ringers=8, minutes=5, band=band).unwrap()
        assert view.used_minutes <= 5
