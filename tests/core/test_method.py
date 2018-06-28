import pytest

from blueline.core.method import Method, MethodError
from blueline.core.row import Row

PLAIN_BOB_MINOR = Method.from_notation("Plain Bob", 6, "x16x16x16,12")
PLAIN_BOB_MAJOR = Method.from_notation("Plain Bob", 8, "x18x18x18x18,12")
CAMBRIDGE_MINOR = Method.from_notation("Cambridge Surprise", 6, "x36x14x12x36x14x56,12")
GRANDSIRE_DOUBLES = Method.from_notation("Grandsire", 5, "3.1.5.1.5.1.5.1.5.1")


class TestBuilding:
    def test_keeps_the_notation_it_was_given(self):
        assert PLAIN_BOB_MINOR.notation == "x16x16x16x16x16x12"

    def test_trims_the_name(self):
        assert Method.from_notation("  Plain Bob  ", 6, "x16x16x16,12").name == "Plain Bob"

    def test_refuses_a_method_with_no_changes(self):
        with pytest.raises(MethodError):
            Method(name="Nothing", stage=6, changes=())

    def test_refuses_a_change_from_another_stage(self):
        from blueline.core.notation import parse_change

        with pytest.raises(MethodError):
            Method(name="Muddle", stage=6, changes=(parse_change("18", 8),))


class TestLeads:
    def test_plain_bob_minor_has_a_twelve_row_lead(self):
        assert PLAIN_BOB_MINOR.lead_length == 12

    def test_plain_bob_major_has_a_sixteen_row_lead(self):
        assert PLAIN_BOB_MAJOR.lead_length == 16

    def test_cambridge_minor_has_a_twenty_four_row_lead(self):
        # The treble dodges its way up and down, so the lead is twice as long
        # as a plain method at the same stage.
        assert CAMBRIDGE_MINOR.lead_length == 24

    def test_a_lead_gives_one_more_row_than_changes(self):
        assert len(PLAIN_BOB_MINOR.lead_rows()) == PLAIN_BOB_MINOR.lead_length + 1

    def test_the_lead_starts_at_rounds_by_default(self):
        assert PLAIN_BOB_MINOR.lead_rows()[0].is_rounds

    def test_a_lead_can_start_anywhere(self):
        start = Row.parse("135264")
        assert PLAIN_BOB_MINOR.lead_rows(start)[0] == start

    def test_refuses_a_start_at_the_wrong_stage(self):
        with pytest.raises(MethodError):
            PLAIN_BOB_MINOR.lead_rows(Row.rounds(8))


class TestLeadHeads:
    def test_plain_bob_minor_lead_head(self):
        assert str(PLAIN_BOB_MINOR.lead_head) == "135264"

    def test_plain_bob_major_lead_head(self):
        assert str(PLAIN_BOB_MAJOR.lead_head) == "13527486"

    def test_cambridge_minor_has_its_own_lead_head(self):
        assert str(CAMBRIDGE_MINOR.lead_head) == "156342"

    def test_cambridge_comes_round_in_the_same_number_of_leads_as_plain_bob(self):
        assert CAMBRIDGE_MINOR.leads_in_course == PLAIN_BOB_MINOR.leads_in_course

    def test_grandsire_doubles_lead_head(self):
        assert str(GRANDSIRE_DOUBLES.lead_head) == "12534"


class TestCourses:
    def test_plain_bob_minor_has_five_leads(self):
        assert PLAIN_BOB_MINOR.leads_in_course == 5

    def test_plain_bob_major_has_seven_leads(self):
        assert PLAIN_BOB_MAJOR.leads_in_course == 7

    def test_plain_bob_minor_course_is_sixty_rows(self):
        assert PLAIN_BOB_MINOR.course_length == 60
        assert len(PLAIN_BOB_MINOR.plain_course()) == 60

    def test_plain_bob_major_course_is_a_hundred_and_twelve(self):
        assert PLAIN_BOB_MAJOR.course_length == 112

    def test_the_course_starts_at_rounds(self):
        assert PLAIN_BOB_MINOR.plain_course()[0].is_rounds

    def test_the_course_does_not_end_on_rounds_again(self):
        assert not PLAIN_BOB_MINOR.plain_course()[-1].is_rounds

    def test_ringing_the_course_brings_it_round(self):
        rows = PLAIN_BOB_MINOR.plain_course()
        last = rows[-1]
        after = PLAIN_BOB_MINOR.changes[-1].apply(last)
        assert after.is_rounds


class TestTruth:
    def test_plain_bob_minor_rings_a_true_course(self):
        assert PLAIN_BOB_MINOR.is_true_course()

    def test_cambridge_minor_rings_a_true_course(self):
        assert CAMBRIDGE_MINOR.is_true_course()

    def test_plain_bob_major_rings_a_true_course(self):
        assert PLAIN_BOB_MAJOR.is_true_course()


class TestBells:
    def test_the_treble_hunts_in_plain_bob(self):
        assert PLAIN_BOB_MINOR.hunt_bells == (1,)

    def test_the_rest_are_working_bells(self):
        assert PLAIN_BOB_MINOR.working_bells == (2, 3, 4, 5, 6)

    def test_grandsire_has_two_hunt_bells(self):
        assert GRANDSIRE_DOUBLES.hunt_bells == (1, 2)

    def test_every_bell_is_hunting_or_working(self):
        both = set(CAMBRIDGE_MINOR.hunt_bells) | set(CAMBRIDGE_MINOR.working_bells)
        assert both == set(range(1, 7))

    def test_grandsire_doubles_course_is_thirty_rows(self):
        assert GRANDSIRE_DOUBLES.course_length == 30

    def test_the_odd_stages_carry_a_covering_tenor(self):
        assert GRANDSIRE_DOUBLES.has_covering_tenor
        assert not PLAIN_BOB_MINOR.has_covering_tenor


class TestPaths:
    def test_the_treble_hunts_up_and_down(self):
        assert PLAIN_BOB_MINOR.path_of(1) == (1, 2, 3, 4, 5, 6, 6, 5, 4, 3, 2, 1, 1)

    def test_a_path_is_as_long_as_the_lead(self):
        assert len(PLAIN_BOB_MINOR.path_of(3)) == PLAIN_BOB_MINOR.lead_length + 1

    def test_the_seconds_place_bell_makes_seconds(self):
        assert PLAIN_BOB_MINOR.path_of(2)[:3] == (2, 1, 1)

    def test_the_treble_dodges_its_way_up_in_a_surprise_method(self):
        assert CAMBRIDGE_MINOR.path_of(1)[:12] == (1, 2, 1, 2, 3, 4, 3, 4, 5, 6, 5, 6)

    def test_the_second_hunts_too_in_grandsire(self):
        assert GRANDSIRE_DOUBLES.path_of(2) == (2, 1, 1, 2, 3, 4, 5, 5, 4, 3, 2)

    def test_refuses_a_bell_that_is_not_there(self):
        with pytest.raises(MethodError):
            PLAIN_BOB_MINOR.path_of(9)

    def test_every_bell_visits_every_place_in_plain_bob(self):
        for bell in PLAIN_BOB_MINOR.working_bells:
            places = set()
            row = Row.rounds(6)
            for _ in range(PLAIN_BOB_MINOR.leads_in_course):
                places.update(r.place_of(bell) for r in PLAIN_BOB_MINOR.lead_rows(row))
                row = row.transposed_by(PLAIN_BOB_MINOR.lead_head)
            assert places == set(range(1, 7))
