from datetime import timedelta

import pytest

from blueline.core.plans import (
    Item,
    Plan,
    PlanError,
    course_item,
    plan_practice,
    ringable_by,
)
from blueline.errors import BluelineError
from blueline.library import standard_methods

ALL = standard_methods()


class TestRingableBy:
    def test_a_band_of_eight_can_ring_major(self):
        found = ringable_by(ALL, 8)
        assert all(method.stage in (7, 8) for method in found)

    def test_a_band_of_eight_can_ring_triples_with_a_cover(self):
        stages = {method.stage for method in ringable_by(ALL, 8)}
        assert 7 in stages

    def test_a_band_of_eight_cannot_ring_minor(self):
        assert 6 not in {method.stage for method in ringable_by(ALL, 8)}

    def test_a_band_of_six_can_ring_minor_and_doubles(self):
        stages = {method.stage for method in ringable_by(ALL, 6)}
        assert stages <= {5, 6}

    def test_a_band_of_seven_cannot_ring_minor(self):
        # Six is even, so the seventh has nothing to cover.
        assert 6 not in {method.stage for method in ringable_by(ALL, 7)}

    def test_too_few_people_is_refused(self):
        with pytest.raises(PlanError, match="not enough people"):
            ringable_by(ALL, 2)

    def test_a_plan_error_is_a_blueline_error(self):
        assert issubclass(PlanError, BluelineError)

    def test_a_band_bigger_than_anything_stored_gets_nothing(self):
        assert ringable_by(ALL, 16) == []


class TestCourseItem:
    def test_it_uses_the_whole_plain_course(self):
        method = next(m for m in ALL if m.stage == 8 and m.name == "Cambridge")
        assert course_item(method).changes == 224

    def test_it_times_the_ringing(self):
        method = next(m for m in ALL if m.stage == 8 and m.name == "Cambridge")
        assert course_item(method).minutes == pytest.approx(224 / 30, abs=1)

    def test_a_faster_band_takes_less_time(self):
        method = next(m for m in ALL if m.stage == 8)
        assert course_item(method, 40).minutes <= course_item(method, 20).minutes

    def test_nothing_takes_less_than_a_minute(self):
        method = next(m for m in ALL if m.stage == 5)
        assert course_item(method).minutes >= 1

    def test_it_reads_as_a_line(self):
        method = next(m for m in ALL if m.stage == 8 and m.name == "Cambridge")
        assert str(course_item(method)).startswith("224 of Cambridge")


class TestPlanPractice:
    def test_it_fills_the_time(self):
        plan = plan_practice(ALL, ringers=8, minutes=60)
        assert plan.minutes <= 60

    def test_it_never_goes_over(self):
        for minutes in (5, 15, 30, 90):
            assert plan_practice(ALL, ringers=8, minutes=minutes).minutes <= minutes

    def test_it_only_picks_what_the_band_can_ring(self):
        plan = plan_practice(ALL, ringers=6, minutes=60)
        assert all(item.method.stage in (5, 6) for item in plan.items)

    def test_the_shortest_comes_first(self):
        plan = plan_practice(ALL, ringers=8, minutes=120)
        minutes = [item.minutes for item in plan.items]
        assert minutes == sorted(minutes)

    def test_it_totals_the_changes(self):
        plan = plan_practice(ALL, ringers=8, minutes=60)
        assert plan.changes == sum(item.changes for item in plan.items)

    def test_it_says_what_is_left(self):
        plan = plan_practice(ALL, ringers=8, minutes=60)
        spent = timedelta(minutes=plan.minutes)
        assert plan.left_over == plan.available - spent

    def test_a_short_practice_fits_less_in(self):
        short = plan_practice(ALL, ringers=8, minutes=10)
        long = plan_practice(ALL, ringers=8, minutes=120)
        assert len(short.items) <= len(long.items)

    def test_a_practice_of_no_time_is_refused(self):
        with pytest.raises(PlanError, match="longer than nothing"):
            plan_practice(ALL, ringers=8, minutes=0)

    def test_a_band_too_small_is_refused(self):
        with pytest.raises(PlanError):
            plan_practice(ALL, ringers=2, minutes=60)

    def test_a_band_nothing_suits_gets_an_empty_plan(self):
        plan = plan_practice(ALL, ringers=16, minutes=60)
        assert plan.items == ()
        assert "nothing this band can ring" in plan.summary()

    def test_the_summary_counts_what_it_chose(self):
        plan = plan_practice(ALL, ringers=8, minutes=60)
        assert "touches" in plan.summary()
        assert "to spare" in plan.summary()

    def test_a_faster_band_fits_more_in(self):
        quick = plan_practice(ALL, ringers=8, minutes=30, speed=40)
        slow = plan_practice(ALL, ringers=8, minutes=30, speed=20)
        assert len(quick.items) >= len(slow.items)


class TestPlanShape:
    def test_an_empty_plan_totals_nothing(self):
        plan = Plan(items=(), ringers=8, available=timedelta(minutes=60), left_over=timedelta())
        assert plan.minutes == 0
        assert plan.changes == 0

    def test_an_item_names_its_method_and_stage(self):
        method = next(m for m in ALL if m.stage == 8 and m.name == "Cambridge")
        assert Item(method=method, changes=224, minutes=8).title == "Cambridge 8"
