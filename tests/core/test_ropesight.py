
from typing import List

import pytest

from blueline.core.ropesight import (
    Blow,
    blows_of,
    dodges_in,
    followed_by_at,
    follows_at,
    leads_in,
    lies_in,
    places_made_in,
    rope_order,
    work_of,
)
from blueline.core.row import Row
from blueline.errors import MethodError
from tests.methods import CAMBRIDGE_MINOR, PLAIN_BOB_MINOR


class TestFollowing:
    def test_the_treble_follows_nobody_when_leading(self):
        assert follows_at(Row.rounds(6), 1) is None

    def test_a_bell_follows_the_one_before_it(self):
        assert follows_at(Row.parse("135264"), 5) == 3

    def test_the_tenor_is_followed_by_nobody(self):
        assert followed_by_at(Row.rounds(6), 6) is None

    def test_a_bell_is_followed_by_the_one_after(self):
        assert followed_by_at(Row.parse("135264"), 5) == 2

    def test_a_bell_that_is_not_there_is_refused(self):
        with pytest.raises(Exception):
            follows_at(Row.rounds(6), 9)


class TestBlow:
    def test_it_knows_when_it_is_leading(self):
        assert Blow(row=0, place=1, follows=None, followed_by=2).is_leading

    def test_it_knows_when_it_is_lying(self):
        assert Blow(row=0, place=6, follows=5, followed_by=None).is_lying

    def test_a_middle_blow_is_neither(self):
        blow = Blow(row=0, place=3, follows=2, followed_by=4)
        assert not blow.is_leading
        assert not blow.is_lying


class TestBlowsOf:
    def test_there_is_one_blow_per_row(self):
        rows = PLAIN_BOB_MINOR.lead_rows()
        assert len(blows_of(rows, 2)) == len(rows)

    def test_the_rows_are_numbered_from_nought(self):
        assert blows_of(PLAIN_BOB_MINOR.lead_rows(), 1)[0].row == 0

    def test_the_treble_starts_leading(self):
        assert blows_of(PLAIN_BOB_MINOR.lead_rows(), 1)[0].is_leading

    def test_the_places_match_the_line(self):
        blows = blows_of(PLAIN_BOB_MINOR.lead_rows(), 3)
        assert [blow.place for blow in blows] == list(PLAIN_BOB_MINOR.path_of(3))


class TestWork:
    def test_the_treble_in_plain_bob_leads_twice_and_lies_twice(self):
        work = work_of(PLAIN_BOB_MINOR, 1)
        assert len(work["leads"]) == 2
        assert len(work["lies"]) == 2

    def test_the_treble_in_plain_bob_never_dodges(self):
        assert work_of(PLAIN_BOB_MINOR, 1)["dodges"] == []

    def test_the_treble_in_cambridge_dodges(self):
        assert work_of(CAMBRIDGE_MINOR, 1)["dodges"]

    def test_the_treble_in_cambridge_dodges_six_times(self):
        # Up in one two, three four and five six, and the same coming down.
        assert len(work_of(CAMBRIDGE_MINOR, 1)["dodges"]) == 6

    def test_a_treble_dodging_method_dodges_once_per_pair_each_way(self):
        from tests.methods import CAMBRIDGE_MAJOR

        assert len(work_of(CAMBRIDGE_MAJOR, 1)["dodges"]) == 8

    def test_the_closing_row_is_not_counted_twice(self):
        # It is the opening row of the next lead, and counting it had the
        # treble leading three times in a lead of Plain Bob.
        assert len(work_of(PLAIN_BOB_MINOR, 1)["leads"]) == 2

    def test_the_second_makes_seconds_in_plain_bob(self):
        assert work_of(PLAIN_BOB_MINOR, 2)["places"]

    def test_every_bell_has_some_work(self):
        for bell in range(1, 7):
            work = work_of(CAMBRIDGE_MINOR, bell)
            assert any(work.values())

    def test_a_bell_that_is_not_there_is_refused(self):
        with pytest.raises(MethodError):
            work_of(PLAIN_BOB_MINOR, 9)

    def test_the_four_kinds_of_work_are_always_reported(self):
        assert set(work_of(PLAIN_BOB_MINOR, 3)) == {"leads", "lies", "dodges", "places"}


def _at_places(places: List[int]) -> List[Blow]:
    """Blows at the given places, for testing the work without a method."""
    return [
        Blow(row=index, place=place, follows=None, followed_by=None)
        for index, place in enumerate(places)
    ]


class TestDodgesAndPlaces:
    def test_standing_still_is_a_place_not_a_dodge(self):
        blows = [
            Blow(row=0, place=2, follows=1, followed_by=3),
            Blow(row=1, place=2, follows=1, followed_by=3),
        ]
        assert places_made_in(blows) == [1]
        assert dodges_in(blows) == []

    def test_a_step_out_and_straight_back_is_a_dodge(self):
        blows = _at_places([3, 4, 3])
        assert dodges_in(blows) == [1]

    def test_hunting_straight_through_is_not(self):
        assert dodges_in(_at_places([3, 4, 5, 6])) == []

    def test_dodges_do_not_overlap(self):
        # A ringer counts one dodge here, not two.
        assert dodges_in(_at_places([1, 2, 1, 2])) == [1]

    def test_two_separate_dodges_are_both_found(self):
        assert len(dodges_in(_at_places([1, 2, 1, 2, 3, 4, 3, 4]))) == 2

    def test_one_blow_on_its_own_has_no_work(self):
        blows = _at_places([1])
        assert dodges_in(blows) == []
        assert places_made_in(blows) == []

    def test_two_blows_cannot_make_a_dodge(self):
        assert dodges_in(_at_places([1, 2])) == []


class TestLeadsAndLies:
    def test_it_finds_every_leading_row(self):
        blows = blows_of(PLAIN_BOB_MINOR.lead_rows()[:-1], 2)
        assert leads_in(blows) == [1, 2]

    def test_it_finds_every_lying_row(self):
        blows = blows_of(PLAIN_BOB_MINOR.lead_rows()[:-1], 1)
        assert lies_in(blows) == [5, 6]


class TestRopeOrder:
    def test_it_is_the_row_the_ropes_go_down_in(self):
        assert rope_order(Row.parse("135264")) == [1, 3, 5, 2, 6, 4]

    def test_it_is_as_long_as_the_stage(self):
        assert len(rope_order(Row.rounds(8))) == 8
