from blueline.service import ringers as service
from blueline.service.results import Reason

CAMBRIDGE = "Cambridge Surprise Major"
PLAIN = "Plain Bob Major"
YORKSHIRE = "Yorkshire Surprise Major"


def a_band(store) -> None:
    for name in ("Ann", "Bob", "Cara", "Dan", "Eve", "Finn"):
        service.add(store, name, can_ring=[CAMBRIDGE, PLAIN])
    service.add(store, "Gus", can_ring=[PLAIN], learning=[CAMBRIDGE])
    service.add(store, "Hana", can_ring=[PLAIN], learning=[YORKSHIRE])


class TestAdding:
    def test_somebody_can_be_added(self, ringers):
        view = service.add(ringers, "Ann", can_ring=[CAMBRIDGE]).unwrap()
        assert view.name == "Ann"
        assert view.can_ring == (CAMBRIDGE,)

    def test_they_are_stored(self, ringers):
        service.add(ringers, "Ann")
        assert ringers.count() == 1

    def test_somebody_who_rings_nothing_yet_is_fine(self, ringers):
        view = service.add(ringers, "New").unwrap()
        assert view.can_ring == ()
        assert view.method_count == 0

    def test_the_same_name_twice_is_a_conflict(self, ringers):
        service.add(ringers, "Ann")
        assert service.add(ringers, "Ann").failure.reason is Reason.ALREADY_EXISTS

    def test_a_name_of_nothing_is_invalid(self, ringers):
        assert service.add(ringers, "   ").failure.reason is Reason.INVALID

    def test_ringing_and_learning_the_same_method_is_invalid(self, ringers):
        result = service.add(ringers, "Ann", can_ring=[CAMBRIDGE], learning=[CAMBRIDGE])
        assert result.failure.reason is Reason.INVALID

    def test_blank_titles_are_dropped(self, ringers):
        view = service.add(ringers, "Ann", can_ring=[CAMBRIDGE, "  ", ""]).unwrap()
        assert view.can_ring == (CAMBRIDGE,)

    def test_nothing_is_stored_when_it_is_refused(self, ringers):
        service.add(ringers, "  ")
        assert ringers.count() == 0


class TestView:
    def test_the_titles_come_back_sorted(self, ringers):
        view = service.add(ringers, "Ann", can_ring=[PLAIN, CAMBRIDGE]).unwrap()
        assert view.can_ring == (CAMBRIDGE, PLAIN)

    def test_the_summary_counts_the_methods(self, ringers):
        view = service.add(ringers, "Ann", can_ring=[PLAIN, CAMBRIDGE]).unwrap()
        assert "2 methods" in view.summary()

    def test_it_mentions_what_they_are_learning(self, ringers):
        view = service.add(ringers, "Gus", learning=[CAMBRIDGE]).unwrap()
        assert "learning" in view.summary()

    def test_somebody_learning_nothing_does_not_mention_it(self, ringers):
        view = service.add(ringers, "Ann", can_ring=[PLAIN]).unwrap()
        assert "learning" not in view.summary()


class TestFetchAndRemove:
    def test_somebody_can_be_fetched(self, ringers):
        service.add(ringers, "Ann", can_ring=[CAMBRIDGE])
        assert service.fetch(ringers, "Ann").unwrap().method_count == 1

    def test_lookup_ignores_case(self, ringers):
        service.add(ringers, "Ann")
        assert service.fetch(ringers, "ann").ok

    def test_somebody_who_is_not_there_is_not_found(self, ringers):
        assert service.fetch(ringers, "Nobody").failure.reason is Reason.NOT_FOUND

    def test_somebody_can_be_removed(self, ringers):
        service.add(ringers, "Ann")
        assert service.remove(ringers, "Ann").ok
        assert service.fetch(ringers, "Ann").failure.reason is Reason.NOT_FOUND

    def test_removing_somebody_who_is_not_there_is_not_found(self, ringers):
        assert service.remove(ringers, "Nobody").failure.reason is Reason.NOT_FOUND

    def test_everybody_comes_back_in_name_order(self, ringers):
        a_band(ringers)
        names = [view.name for view in service.everybody(ringers).unwrap()]
        assert names == sorted(names)


class TestLearnt:
    def test_it_moves_a_method_across(self, ringers):
        service.add(ringers, "Gus", can_ring=[PLAIN], learning=[CAMBRIDGE])
        view = service.learnt(ringers, "Gus", CAMBRIDGE).unwrap()
        assert CAMBRIDGE in view.can_ring
        assert CAMBRIDGE not in view.learning

    def test_it_leaves_the_rest_alone(self, ringers):
        service.add(ringers, "Gus", can_ring=[PLAIN], learning=[CAMBRIDGE, YORKSHIRE])
        view = service.learnt(ringers, "Gus", CAMBRIDGE).unwrap()
        assert PLAIN in view.can_ring
        assert YORKSHIRE in view.learning

    def test_learning_something_new_outright_works(self, ringers):
        service.add(ringers, "Ann")
        assert CAMBRIDGE in service.learnt(ringers, "Ann", CAMBRIDGE).unwrap().can_ring

    def test_it_is_saved(self, ringers):
        service.add(ringers, "Gus", learning=[CAMBRIDGE])
        service.learnt(ringers, "Gus", CAMBRIDGE)
        assert CAMBRIDGE in service.fetch(ringers, "Gus").unwrap().can_ring

    def test_a_method_of_nothing_is_invalid(self, ringers):
        service.add(ringers, "Ann")
        assert service.learnt(ringers, "Ann", "  ").failure.reason is Reason.INVALID

    def test_somebody_who_is_not_there_is_not_found(self, ringers):
        assert service.learnt(ringers, "Nobody", CAMBRIDGE).failure.reason is Reason.NOT_FOUND


class TestWhoCanRing:
    def test_it_lists_them(self, ringers):
        a_band(ringers)
        assert service.who_can_ring(ringers, CAMBRIDGE).unwrap() == [
            "Ann",
            "Bob",
            "Cara",
            "Dan",
            "Eve",
            "Finn",
        ]

    def test_a_learner_is_not_counted(self, ringers):
        a_band(ringers)
        assert "Gus" not in service.who_can_ring(ringers, CAMBRIDGE).unwrap()

    def test_a_method_nobody_rings_finds_nobody(self, ringers):
        a_band(ringers)
        assert service.who_can_ring(ringers, YORKSHIRE).unwrap() == []

    def test_a_title_inside_a_longer_one_is_not_a_match(self, ringers):
        # The query narrows on the text and the service checks properly.
        service.add(ringers, "Ann", can_ring=["Cambridge Surprise Major"])
        assert service.who_can_ring(ringers, "Cambridge Surprise").unwrap() == []


class TestBandCapability:
    def test_a_band_carrying_one_learner_cannot_yet(self, ringers):
        a_band(ringers)
        assert not service.can_the_band_ring(ringers, CAMBRIDGE, 8).unwrap()

    def test_once_the_learner_has_it_they_can(self, ringers):
        a_band(ringers)
        service.learnt(ringers, "Gus", CAMBRIDGE)
        assert service.can_the_band_ring(ringers, CAMBRIDGE, 8).unwrap()

    def test_everybody_ringing_it_is_certainly_enough(self, ringers):
        a_band(ringers)
        assert service.can_the_band_ring(ringers, PLAIN, 8).unwrap()

    def test_it_picks_what_the_band_can_get_through(self, ringers, loaded):
        a_band(ringers)
        found = service.what_can_be_rung(ringers, loaded, 8).unwrap()
        assert "Plain Bob Major" in found
        assert "Cambridge Surprise Major" not in found

    def test_a_band_too_small_is_invalid(self, ringers, loaded):
        service.add(ringers, "Ann")
        assert service.what_can_be_rung(ringers, loaded, 8).failure.reason is Reason.INVALID


class TestLearning:
    def test_it_groups_by_method(self, ringers):
        a_band(ringers)
        found = service.learning(ringers).unwrap()
        assert found[CAMBRIDGE] == ["Gus"]
        assert found[YORKSHIRE] == ["Hana"]

    def test_a_band_learning_nothing_has_nothing(self, ringers):
        service.add(ringers, "Ann", can_ring=[PLAIN])
        assert service.learning(ringers).unwrap() == {}
