import pytest

from blueline.core.coursing import (
    CoursingError,
    as_text,
    courses_after,
    courses_before,
    coursing_order,
    coursing_order_of,
    coursing_pairs,
    coursing_places,
    is_same_ring,
    rotate_to,
)
from blueline.core.row import Row
from tests.methods import (
    CAMBRIDGE_MAJOR,
    CAMBRIDGE_MINOR,
    DOUBLE_NORWICH,
    GRANDSIRE_DOUBLES,
    PLAIN_BOB_DOUBLES,
    PLAIN_BOB_MAJOR,
    PLAIN_BOB_MINOR,
)


class TestCoursingPlaces:
    def test_major_reads_the_odd_places_down_then_the_even_ones_up(self):
        assert coursing_places(8) == (7, 5, 3, 2, 4, 6, 8)

    def test_minor(self):
        assert coursing_places(6) == (5, 3, 2, 4, 6)

    def test_doubles_starts_at_the_back(self):
        assert coursing_places(5) == (5, 3, 2, 4)

    def test_leading_is_left_out(self):
        assert 1 not in coursing_places(8)

    def test_every_other_place_appears_once(self):
        places = coursing_places(8)
        assert sorted(places) == list(range(2, 9))


class TestKnownOrders:
    def test_plain_bob_major_is_the_one_everybody_learns(self):
        assert as_text(coursing_order(PLAIN_BOB_MAJOR)) == "8753246"

    def test_plain_bob_minor(self):
        assert as_text(coursing_order(PLAIN_BOB_MINOR)) == "65324"

    def test_plain_bob_doubles(self):
        assert as_text(coursing_order(PLAIN_BOB_DOUBLES)) == "5324"

    def test_cambridge_major_has_the_same_ring_as_plain_bob(self):
        # Different lead head, same lead head group, so the same coursing order.
        assert as_text(coursing_order(CAMBRIDGE_MAJOR)) == "8753246"

    def test_cambridge_minor_too(self):
        assert as_text(coursing_order(CAMBRIDGE_MINOR)) == "65324"

    def test_double_norwich_agrees_as_well(self):
        assert as_text(coursing_order(DOUBLE_NORWICH)) == "8753246"

    def test_grandsire_leaves_out_both_hunt_bells(self):
        order = coursing_order(GRANDSIRE_DOUBLES)
        assert 1 not in order
        assert 2 not in order
        assert as_text(order) == "534"


class TestShape:
    def test_it_starts_at_the_tenor(self):
        for method in (PLAIN_BOB_MAJOR, CAMBRIDGE_MAJOR, PLAIN_BOB_MINOR):
            order = coursing_order(method)
            assert order[0] == max(order)

    def test_it_holds_every_working_bell_once(self):
        order = coursing_order(PLAIN_BOB_MAJOR)
        assert sorted(order) == list(PLAIN_BOB_MAJOR.working_bells)

    def test_refuses_a_lead_head_with_nothing_coursing(self):
        with pytest.raises(CoursingError):
            coursing_order_of(Row.rounds(6), hunt_bells=tuple(range(1, 7)))


class TestNeighbours:
    def test_finds_the_bell_that_courses_after(self):
        assert courses_after((8, 7, 5, 3, 2, 4, 6), 8) == 7

    def test_wraps_round_at_the_end(self):
        assert courses_after((8, 7, 5, 3, 2, 4, 6), 6) == 8

    def test_finds_the_bell_that_courses_before(self):
        assert courses_before((8, 7, 5, 3, 2, 4, 6), 7) == 8

    def test_wraps_round_the_other_way(self):
        assert courses_before((8, 7, 5, 3, 2, 4, 6), 8) == 6

    def test_refuses_a_bell_that_is_not_coursing(self):
        with pytest.raises(CoursingError):
            courses_after((8, 7, 5), 4)
        with pytest.raises(CoursingError):
            courses_before((8, 7, 5), 4)

    def test_pairs_every_bell_with_the_next(self):
        pairs = coursing_pairs((8, 7, 5))
        assert pairs == [(8, 7), (7, 5), (5, 8)]

    def test_there_are_as_many_pairs_as_bells(self):
        order = coursing_order(PLAIN_BOB_MAJOR)
        assert len(coursing_pairs(order)) == len(order)


class TestRotation:
    def test_writes_the_ring_from_another_bell(self):
        assert rotate_to((8, 7, 5, 3, 2, 4, 6), 3) == (3, 2, 4, 6, 8, 7, 5)

    def test_rotating_to_the_first_bell_leaves_it_alone(self):
        order = (8, 7, 5, 3, 2, 4, 6)
        assert rotate_to(order, 8) == order

    def test_refuses_a_bell_that_is_not_there(self):
        with pytest.raises(CoursingError):
            rotate_to((8, 7, 5), 2)

    def test_a_rotated_ring_is_the_same_ring(self):
        order = coursing_order(PLAIN_BOB_MAJOR)
        assert is_same_ring(order, rotate_to(order, 3))

    def test_a_different_ring_is_not(self):
        assert not is_same_ring((8, 7, 5, 3, 2, 4, 6), (8, 5, 2, 6, 7, 3, 4))

    def test_rings_of_different_lengths_are_not_the_same(self):
        assert not is_same_ring((8, 7, 5), (8, 7, 5, 3))

    def test_rings_of_different_bells_are_not_the_same(self):
        assert not is_same_ring((8, 7, 5), (8, 7, 4))
