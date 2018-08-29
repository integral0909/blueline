"""The grid and the line have to agree with each other and with the rows."""

from __future__ import annotations

import pytest

from blueline.core.lines import leads_of_course, marked_grid, place_bell_order
from blueline.core.ropesight import blows_of, work_of
from blueline.core.row import Row
from tests.methods import ALL_METHODS, CAMBRIDGE_MAJOR, CAMBRIDGE_MINOR, method_id


@pytest.mark.parametrize("method", ALL_METHODS, ids=method_id)
class TestAcrossEveryMethod:
    def test_the_grid_marks_the_bell_where_the_line_says(self, method):
        rows = method.lead_rows()
        for bell in (1, method.stage):
            grid = marked_grid(rows, bell)
            for row_index, line in enumerate(grid):
                assert line.index("*") + 1 == rows[row_index].place_of(bell)

    def test_the_work_adds_up_to_the_lead(self, method):
        blows = blows_of(method.lead_rows()[:-1], 1)
        assert len(blows) == method.lead_length

    def test_every_bell_ends_where_the_lead_head_says(self, method):
        head = method.lead_head
        for bell in range(1, method.stage + 1):
            assert method.lead_rows()[-1].place_of(bell) == head.place_of(bell)

    def test_the_place_bell_order_covers_the_working_bells(self, method):
        order = place_bell_order(method)
        assert len(order) == method.leads_in_course

    def test_the_course_is_its_leads_joined_up(self, method):
        leads = leads_of_course(method)
        joined = [leads[0][0]]
        for lead in leads:
            joined.extend(lead[1:])
        assert len(joined) == method.course_length + 1
        assert joined[-1].is_rounds


class TestTrebleAgainstClass:
    def test_a_plain_treble_visits_each_place_twice(self):
        from tests.methods import PLAIN_BOB_MAJOR

        blows = blows_of(PLAIN_BOB_MAJOR.lead_rows()[:-1], 1)
        places = [blow.place for blow in blows]
        for place in range(1, 9):
            assert places.count(place) == 2

    def test_a_dodging_treble_visits_each_place_four_times(self):
        blows = blows_of(CAMBRIDGE_MAJOR.lead_rows()[:-1], 1)
        places = [blow.place for blow in blows]
        for place in range(1, 9):
            assert places.count(place) == 4

    def test_a_dodging_treble_dodges_once_per_pair_each_way(self):
        assert len(work_of(CAMBRIDGE_MINOR, 1)["dodges"]) == CAMBRIDGE_MINOR.stage
        assert len(work_of(CAMBRIDGE_MAJOR, 1)["dodges"]) == CAMBRIDGE_MAJOR.stage


class TestGridShape:
    def test_every_line_is_as_wide_as_the_stage(self):
        for line in marked_grid(CAMBRIDGE_MAJOR.lead_rows(), 3):
            assert len(line) == 8

    def test_the_unmarked_bells_are_still_there(self):
        row = Row.parse("13527486")
        line = marked_grid([row], 5)[0]
        assert sorted(line.replace("*", "")) == sorted("1327486")

    def test_marking_the_treble_and_the_tenor_differ(self):
        rows = CAMBRIDGE_MAJOR.lead_rows()
        assert marked_grid(rows, 1) != marked_grid(rows, 8)


@pytest.mark.parametrize("method", ALL_METHODS, ids=method_id)
class TestWorkAcrossEveryMethod:
    def test_no_bell_dodges_and_makes_a_place_in_the_same_row(self, method):
        for bell in range(1, method.stage + 1):
            work = work_of(method, bell)
            assert not set(work["dodges"]) & set(work["places"])

    def test_every_row_of_work_is_inside_the_lead(self, method):
        for bell in range(1, method.stage + 1):
            for rows in work_of(method, bell).values():
                assert all(0 <= row < method.lead_length for row in rows)

    def test_leading_and_lying_never_happen_at_once(self, method):
        for bell in range(1, method.stage + 1):
            work = work_of(method, bell)
            assert not set(work["leads"]) & set(work["lies"])

    def test_every_bell_leads_at_some_point_in_the_course(self, method):
        leads = leads_of_course(method)
        led = set()
        for lead in leads:
            for row in lead[:-1]:
                led.add(row[1])
        assert led == set(range(1, method.stage + 1))

    def test_the_treble_leads_in_every_lead(self, method):
        for lead in leads_of_course(method):
            assert any(row[1] == 1 for row in lead[:-1])
