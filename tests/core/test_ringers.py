
from typing import List

import pytest

from blueline.core.ringers import (
    Ringer,
    RingerError,
    enough_for,
    learning_together,
    what_the_band_can_ring,
    who_can_ring,
    who_is_learning,
)
from blueline.errors import BluelineError

CAMBRIDGE = "Cambridge Surprise Major"
YORKSHIRE = "Yorkshire Surprise Major"
PLAIN = "Plain Bob Major"


def a_band() -> List[Ringer]:
    return [
        Ringer(name="Ann", can_ring=frozenset({CAMBRIDGE, PLAIN})),
        Ringer(name="Bob", can_ring=frozenset({CAMBRIDGE, PLAIN})),
        Ringer(name="Cara", can_ring=frozenset({CAMBRIDGE, PLAIN})),
        Ringer(name="Dan", can_ring=frozenset({CAMBRIDGE, PLAIN})),
        Ringer(name="Eve", can_ring=frozenset({CAMBRIDGE, PLAIN})),
        Ringer(name="Finn", can_ring=frozenset({CAMBRIDGE, PLAIN})),
        Ringer(name="Gus", can_ring=frozenset({PLAIN}), learning=frozenset({CAMBRIDGE})),
        Ringer(name="Hana", can_ring=frozenset({PLAIN}), learning=frozenset({YORKSHIRE})),
    ]


class TestRinger:
    def test_a_ringer_has_to_have_a_name(self):
        with pytest.raises(RingerError, match="a name"):
            Ringer(name="   ")

    def test_nobody_rings_and_learns_the_same_method(self):
        with pytest.raises(RingerError, match="both"):
            Ringer(
                name="Ann",
                can_ring=frozenset({CAMBRIDGE}),
                learning=frozenset({CAMBRIDGE}),
            )

    def test_it_says_what_somebody_can_ring(self):
        ringer = Ringer(name="Ann", can_ring=frozenset({CAMBRIDGE}))
        assert ringer.rings(CAMBRIDGE)
        assert not ringer.rings(YORKSHIRE)

    def test_matching_ignores_case_and_space(self):
        ringer = Ringer(name="Ann", can_ring=frozenset({CAMBRIDGE}))
        assert ringer.rings("  cambridge surprise major ")

    def test_it_says_what_somebody_is_learning(self):
        ringer = Ringer(name="Gus", learning=frozenset({CAMBRIDGE}))
        assert ringer.is_learning(CAMBRIDGE)
        assert not ringer.rings(CAMBRIDGE)

    def test_knowing_anything_covers_both(self):
        ringer = Ringer(name="Gus", learning=frozenset({CAMBRIDGE}))
        assert ringer.knows_anything_of(CAMBRIDGE)

    def test_it_knows_nothing_of_a_method_it_has_never_seen(self):
        assert not Ringer(name="Ann").knows_anything_of(CAMBRIDGE)

    def test_a_ringer_error_is_a_blueline_error(self):
        assert issubclass(RingerError, BluelineError)

    def test_it_reads_as_a_name_and_a_count(self):
        ringer = Ringer(name="Ann", can_ring=frozenset({CAMBRIDGE, PLAIN}))
        assert str(ringer) == "Ann (2 methods)"


class TestLearnt:
    def test_learning_something_moves_it_across(self):
        gus = Ringer(name="Gus", learning=frozenset({CAMBRIDGE}))
        after = gus.learnt(CAMBRIDGE)
        assert after.rings(CAMBRIDGE)
        assert not after.is_learning(CAMBRIDGE)

    def test_it_leaves_the_rest_alone(self):
        gus = Ringer(
            name="Gus",
            can_ring=frozenset({PLAIN}),
            learning=frozenset({CAMBRIDGE, YORKSHIRE}),
        )
        after = gus.learnt(CAMBRIDGE)
        assert after.rings(PLAIN)
        assert after.is_learning(YORKSHIRE)

    def test_learning_something_new_outright_works(self):
        assert Ringer(name="Ann").learnt(CAMBRIDGE).rings(CAMBRIDGE)

    def test_the_original_is_left_alone(self):
        gus = Ringer(name="Gus", learning=frozenset({CAMBRIDGE}))
        gus.learnt(CAMBRIDGE)
        assert gus.is_learning(CAMBRIDGE)


class TestWhoCanRing:
    def test_it_lists_them_in_name_order(self):
        assert who_can_ring(a_band(), CAMBRIDGE) == [
            "Ann",
            "Bob",
            "Cara",
            "Dan",
            "Eve",
            "Finn",
        ]

    def test_a_method_nobody_rings_lists_nobody(self):
        assert who_can_ring(a_band(), YORKSHIRE) == []

    def test_it_lists_who_is_learning(self):
        assert who_is_learning(a_band(), CAMBRIDGE) == ["Gus"]

    def test_learners_are_not_counted_as_able(self):
        assert "Gus" not in who_can_ring(a_band(), CAMBRIDGE)


class TestEnoughFor:
    def test_a_band_carrying_one_learner_is_enough(self):
        # Six can ring it and Gus is learning, which is the usual practice.
        assert enough_for(a_band(), CAMBRIDGE, stage=8) is False

    def test_everybody_but_one_is_enough(self):
        band = a_band()
        band[7] = band[7].learnt(CAMBRIDGE)
        assert enough_for(band, CAMBRIDGE, stage=8)

    def test_everybody_ringing_it_is_certainly_enough(self):
        assert enough_for(a_band(), PLAIN, stage=8)

    def test_a_band_too_small_is_never_enough(self):
        assert not enough_for(a_band()[:4], PLAIN, stage=8)

    def test_nobody_ringing_it_is_not_enough(self):
        assert not enough_for(a_band(), YORKSHIRE, stage=8)


class TestWhatTheBandCanRing:
    def test_it_picks_what_they_can_get_through(self):
        titles = [CAMBRIDGE, YORKSHIRE, PLAIN]
        assert what_the_band_can_ring(a_band(), titles, stage=8) == [PLAIN]

    def test_it_comes_back_sorted(self):
        band = a_band()
        band[6] = band[6].learnt(CAMBRIDGE)
        band[7] = band[7].learnt(CAMBRIDGE)
        found = what_the_band_can_ring(band, [YORKSHIRE, PLAIN, CAMBRIDGE], stage=8)
        assert found == sorted(found)

    def test_nothing_suitable_gives_nothing(self):
        assert what_the_band_can_ring(a_band(), [YORKSHIRE], stage=8) == []


class TestLearningTogether:
    def test_it_groups_by_method(self):
        found = learning_together(a_band())
        assert found[CAMBRIDGE] == ["Gus"]
        assert found[YORKSHIRE] == ["Hana"]

    def test_two_people_on_the_same_method_come_out_together(self):
        band = a_band()
        band[0] = Ringer(name="Ann", learning=frozenset({YORKSHIRE}))
        assert learning_together(band)[YORKSHIRE] == ["Ann", "Hana"]

    def test_a_band_learning_nothing_has_nothing(self):
        band = [Ringer(name="Ann", can_ring=frozenset({PLAIN}))]
        assert learning_together(band) == {}

    def test_the_methods_come_back_sorted(self):
        found = learning_together(a_band())
        assert list(found) == sorted(found)
