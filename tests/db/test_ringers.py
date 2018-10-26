import pytest

from blueline.core.ringers import Ringer
from blueline.db.repositories import RingerRepository, to_ringer, to_stored_ringer
from blueline.errors import LibraryError

CAMBRIDGE = "Cambridge Surprise Major"
PLAIN = "Plain Bob Major"
YORKSHIRE = "Yorkshire Surprise Major"

ANN = Ringer(name="Ann", can_ring=frozenset({CAMBRIDGE, PLAIN}))
GUS = Ringer(name="Gus", can_ring=frozenset({PLAIN}), learning=frozenset({CAMBRIDGE}))


@pytest.fixture()
def ringers(session) -> RingerRepository:
    return RingerRepository(session)


class TestConversion:
    def test_titles_flatten_to_lines(self):
        stored = to_stored_ringer(ANN)
        assert stored.can_ring.splitlines() == [CAMBRIDGE, PLAIN]

    def test_they_are_sorted_so_equal_sets_store_alike(self):
        one = to_stored_ringer(Ringer(name="Ann", can_ring=frozenset({PLAIN, CAMBRIDGE})))
        two = to_stored_ringer(Ringer(name="Ann", can_ring=frozenset({CAMBRIDGE, PLAIN})))
        assert one.can_ring == two.can_ring

    def test_it_goes_round_trip(self):
        assert to_ringer(to_stored_ringer(GUS)) == GUS

    def test_somebody_who_rings_nothing_stores_as_nothing(self):
        stored = to_stored_ringer(Ringer(name="New"))
        assert stored.can_ring == ""
        assert to_ringer(stored).can_ring == frozenset()

    def test_blank_lines_do_not_become_titles(self):
        from blueline.db.models import StoredRinger

        stored = StoredRinger(name="Ann", can_ring=f"{CAMBRIDGE}\n\n  \n{PLAIN}", learning="")
        assert to_ringer(stored).can_ring == frozenset({CAMBRIDGE, PLAIN})


class TestStoring:
    def test_one_can_be_stored(self, ringers):
        ringers.add(ANN)
        assert ringers.count() == 1

    def test_it_can_be_fetched_back(self, ringers):
        ringers.add(ANN)
        assert to_ringer(ringers.get("Ann")).rings(CAMBRIDGE)

    def test_lookup_ignores_case_and_space(self, ringers):
        ringers.add(ANN)
        assert ringers.get("  ann ")

    def test_the_same_name_twice_is_refused(self, ringers):
        ringers.add(ANN)
        with pytest.raises(LibraryError, match="already"):
            ringers.add(ANN)

    def test_find_gives_nothing_rather_than_raising(self, ringers):
        assert ringers.find("Nobody") is None

    def test_get_names_who_was_asked_for(self, ringers):
        with pytest.raises(LibraryError, match="Nobody"):
            ringers.get("Nobody")

    def test_one_can_be_removed(self, ringers, session):
        ringers.add(ANN)
        ringers.remove("Ann")
        session.flush()
        assert ringers.count() == 0

    def test_removing_somebody_who_is_not_there_complains(self, ringers):
        with pytest.raises(LibraryError):
            ringers.remove("Nobody")


class TestSaving:
    def test_saving_somebody_new_adds_them(self, ringers):
        ringers.save(ANN)
        assert ringers.count() == 1

    def test_saving_again_replaces_what_was_there(self, ringers):
        ringers.save(GUS)
        ringers.save(GUS.learnt(CAMBRIDGE))
        assert ringers.count() == 1
        assert to_ringer(ringers.get("Gus")).rings(CAMBRIDGE)

    def test_the_old_learning_is_dropped(self, ringers):
        ringers.save(GUS)
        ringers.save(GUS.learnt(CAMBRIDGE))
        assert not to_ringer(ringers.get("Gus")).is_learning(CAMBRIDGE)


class TestListing:
    @pytest.fixture()
    def loaded(self, ringers):
        for ringer in (GUS, ANN):
            ringers.add(ringer)
        return ringers

    def test_they_come_back_in_name_order(self, loaded):
        assert [stored.name for stored in loaded.all()] == ["Ann", "Gus"]

    def test_the_band_comes_back_as_the_core_type(self, loaded):
        band = loaded.band()
        assert all(isinstance(ringer, Ringer) for ringer in band)

    def test_it_narrows_by_what_somebody_rings(self, loaded):
        found = loaded.who_rings(CAMBRIDGE)
        assert [stored.name for stored in found] == ["Ann"]

    def test_a_learner_is_not_counted_as_ringing_it(self, loaded):
        assert "Gus" not in [stored.name for stored in loaded.who_rings(CAMBRIDGE)]

    def test_a_method_nobody_rings_finds_nobody(self, loaded):
        assert loaded.who_rings(YORKSHIRE) == []

    def test_an_empty_repository_holds_nobody(self, ringers):
        assert ringers.all() == []
        assert ringers.band() == []
