import pytest

from blueline.core.calls import plain_bob_calls
from blueline.core.quarters import (
    Target,
    find_for,
    leads_needed,
    peal_target,
    quarter_target,
    reachable,
)
from blueline.core.touch import parse_calling
from blueline.core.truth import extent_length, prove_touch
from tests.methods import (
    CAMBRIDGE_MINOR,
    PLAIN_BOB_DOUBLES,
    PLAIN_BOB_MAJOR,
    PLAIN_BOB_MINOR,
)

PB5 = plain_bob_calls(5)
PB6 = plain_bob_calls(6)


class TestTarget:
    def test_a_target_with_no_tolerance_is_exact(self):
        target = Target(length=1260)
        assert target.shortest == 1260
        assert target.longest == 1260

    def test_a_tolerance_widens_it_both_ways(self):
        target = Target(length=1260, tolerance=20)
        assert target.shortest == 1240
        assert target.longest == 1280

    def test_it_accepts_what_is_inside(self):
        target = Target(length=1260, tolerance=20)
        assert target.accepts(1260)
        assert target.accepts(1240)
        assert target.accepts(1280)

    def test_it_refuses_what_is_outside(self):
        target = Target(length=1260, tolerance=20)
        assert not target.accepts(1239)
        assert not target.accepts(1281)

    def test_a_tolerance_never_takes_it_below_one(self):
        assert Target(length=5, tolerance=100).shortest == 1

    def test_a_length_of_nothing_is_refused(self):
        with pytest.raises(ValueError, match="cannot aim"):
            Target(length=0)

    def test_a_negative_tolerance_is_refused(self):
        with pytest.raises(ValueError, match="tolerance"):
            Target(length=1260, tolerance=-1)

    def test_an_exact_target_reads_as_a_number(self):
        assert str(Target(length=1260)) == "1260"

    def test_a_loose_one_says_so(self):
        assert str(Target(length=1260, tolerance=20)) == "1260 give or take 20"


class TestNamedTargets:
    def test_a_quarter_of_triples_is_twelve_sixty(self):
        assert quarter_target(7).length == 1260

    def test_a_quarter_of_major_is_twelve_fifty(self):
        assert quarter_target(8).length == 1250

    def test_a_peal_of_major_is_five_thousand(self):
        assert peal_target(8).length == 5000

    def test_a_tolerance_can_be_given(self):
        assert quarter_target(8, tolerance=50).longest == 1300


class TestReachable:
    def test_nothing_longer_than_the_extent_is_reachable(self):
        # A true 1260 of minor does not exist, because there are only 720
        # rows to ring.
        assert not reachable(PLAIN_BOB_MINOR, Target(1260))
        assert not reachable(PLAIN_BOB_DOUBLES, Target(1260))

    def test_the_extent_itself_is_reachable(self):
        assert reachable(PLAIN_BOB_MINOR, Target(extent_length(6)))

    def test_a_length_that_is_not_a_whole_number_of_leads_is_not(self):
        # A quarter of major is nominally 1250 and a lead is 16 changes, which
        # is why major quarters get rung at 1248 or 1280.
        assert not reachable(PLAIN_BOB_MAJOR, Target(1250))

    def test_a_length_that_is_reachable_says_so(self):
        assert reachable(PLAIN_BOB_MAJOR, Target(1248))

    def test_a_tolerance_can_bring_it_into_range(self):
        assert reachable(PLAIN_BOB_MAJOR, Target(1250, tolerance=2))

    def test_cambridge_minor_cannot_reach_a_quarter(self):
        # Its lead is 24 changes and 1260 does not divide by 24.
        assert not reachable(CAMBRIDGE_MINOR, quarter_target(6))


class TestLeadsNeeded:
    def test_it_works_out_the_fewest_and_the_most(self):
        assert leads_needed(PLAIN_BOB_MINOR, Target(720)) == (60, 60)

    def test_a_tolerance_widens_the_range(self):
        fewest, most = leads_needed(PLAIN_BOB_MINOR, Target(720, tolerance=24))
        assert fewest < most

    def test_a_target_shorter_than_a_lead_still_needs_one(self):
        assert leads_needed(PLAIN_BOB_MINOR, Target(5))[0] == 1


class TestFindFor:
    def test_an_unreachable_target_is_answered_without_searching(self):
        found, exhausted = find_for(CAMBRIDGE_MINOR, PB6, quarter_target(6))
        assert found == []
        assert exhausted

    def test_it_finds_a_touch_at_the_target_length(self):
        found, _ = find_for(PLAIN_BOB_DOUBLES, PB5, Target(120), max_found=1)
        assert found
        assert found[0].length == 120

    def test_what_it_finds_is_true_and_comes_round(self):
        found, _ = find_for(PLAIN_BOB_DOUBLES, PB5, Target(120), max_found=1)
        touch = parse_calling(PLAIN_BOB_DOUBLES, PB5, found[0].calling)
        assert touch.comes_round()
        assert prove_touch(touch).is_true

    def test_everything_it_finds_is_inside_the_target(self):
        target = Target(120, tolerance=20)
        found, _ = find_for(PLAIN_BOB_DOUBLES, PB5, target, max_found=4)
        assert all(target.accepts(entry.length) for entry in found)

    def test_the_calls_can_be_restricted(self):
        found, _ = find_for(PLAIN_BOB_DOUBLES, PB5, Target(120), max_found=2, allowed="p-")
        assert all("s" not in entry.calling for entry in found)
