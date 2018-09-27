import pytest

from blueline.core.bobs import (
    Position,
    PositionError,
    calling_from,
    name_for_place,
    position_named,
    positions_in,
    positions_of,
    tenor_places,
)
from blueline.errors import BluelineError
from tests.methods import (
    ALL_METHODS,
    CAMBRIDGE_MAJOR,
    PLAIN_BOB_MAJOR,
    PLAIN_BOB_MINOR,
    method_id,
)


class TestNaming:
    def test_the_tenor_at_the_back_is_home(self):
        assert name_for_place(8, 8) == "Home"

    def test_one_below_the_back_is_wrong(self):
        assert name_for_place(7, 8) == "Wrong"

    def test_two_below_is_middle(self):
        assert name_for_place(6, 8) == "Middle"

    def test_the_tenor_running_in_is_before(self):
        assert name_for_place(2, 8) == "Before"

    def test_the_names_move_with_the_stage(self):
        assert name_for_place(6, 6) == "Home"
        assert name_for_place(5, 6) == "Wrong"

    def test_anything_else_gets_its_place(self):
        assert name_for_place(4, 8) == "Fourths"
        assert name_for_place(3, 8) == "Thirds"


class TestTenorPlaces:
    @pytest.mark.parametrize("method", ALL_METHODS, ids=method_id)
    def test_there_is_one_per_lead(self, method):
        assert len(tenor_places(method)) == method.leads_in_course

    @pytest.mark.parametrize("method", ALL_METHODS, ids=method_id)
    def test_the_tenor_ends_at_home(self, method):
        assert tenor_places(method)[-1] == method.stage

    def test_it_visits_every_place_at_major(self):
        assert sorted(tenor_places(PLAIN_BOB_MAJOR)) == list(range(2, 9))


class TestPositions:
    @pytest.mark.parametrize("method", ALL_METHODS, ids=method_id)
    def test_the_last_lead_is_always_home(self, method):
        assert positions_of(method)[-1].name == "Home"

    def test_every_lead_is_named(self):
        assert len(positions_of(CAMBRIDGE_MAJOR)) == CAMBRIDGE_MAJOR.leads_in_course

    def test_the_leads_are_numbered_from_one(self):
        assert positions_of(PLAIN_BOB_MAJOR)[0].lead == 1

    def test_no_two_positions_share_a_name_at_major(self):
        names = [position.name for position in positions_of(PLAIN_BOB_MAJOR)]
        assert len(set(names)) == len(names)

    def test_cambridge_and_plain_bob_name_the_same_positions(self):
        # Different leads, same names, because the names follow the tenor.
        plain = {position.name for position in positions_of(PLAIN_BOB_MAJOR)}
        surprise = {position.name for position in positions_of(CAMBRIDGE_MAJOR)}
        assert plain == surprise

    def test_but_they_fall_at_different_leads(self):
        plain = {p.name: p.lead for p in positions_of(PLAIN_BOB_MAJOR)}
        surprise = {p.name: p.lead for p in positions_of(CAMBRIDGE_MAJOR)}
        assert plain["Wrong"] != surprise["Wrong"]

    def test_it_reads_as_a_line(self):
        text = str(Position(name="Home", lead=7, tenor_place=8))
        assert text == "Home (lead 7, tenor in 8)"


class TestPositionNamed:
    def test_it_finds_a_position(self):
        assert position_named(PLAIN_BOB_MAJOR, "Home").lead == 7

    def test_it_ignores_case_and_space(self):
        assert position_named(PLAIN_BOB_MAJOR, "  home ").name == "Home"

    def test_a_name_it_does_not_know_is_refused(self):
        with pytest.raises(PositionError, match="no calling position"):
            position_named(PLAIN_BOB_MAJOR, "Sideways")

    def test_the_complaint_lists_what_there_is(self):
        with pytest.raises(PositionError, match="Home"):
            position_named(PLAIN_BOB_MAJOR, "Sideways")

    def test_a_position_error_is_a_blueline_error(self):
        assert issubclass(PositionError, BluelineError)


class TestCallingFrom:
    def test_one_call_makes_one_course(self):
        calling = calling_from(PLAIN_BOB_MAJOR, ["Home"])
        assert len(calling) == 7
        assert calling == "pppppp-"

    def test_calls_within_a_course_stay_in_it(self):
        calling = calling_from(PLAIN_BOB_MAJOR, ["Wrong", "Home"])
        assert len(calling) == 7
        assert calling.count("-") == 2

    def test_repeating_a_position_runs_on_into_another_course(self):
        # Home comes once a course, so two of them is two courses. Collapsing
        # them would quietly turn three calls into two.
        calling = calling_from(PLAIN_BOB_MAJOR, ["Wrong", "Home", "Home"])
        assert len(calling) == 14
        assert calling.count("-") == 3

    def test_going_backwards_also_starts_a_new_course(self):
        calling = calling_from(PLAIN_BOB_MAJOR, ["Home", "Wrong"])
        assert len(calling) == 14

    def test_calling_nothing_gives_a_plain_course(self):
        assert calling_from(PLAIN_BOB_MAJOR, []) == "p" * 7

    def test_the_symbol_can_be_something_else(self):
        assert "s" in calling_from(PLAIN_BOB_MAJOR, ["Home"], symbol="s")

    def test_a_position_it_does_not_know_is_refused(self):
        with pytest.raises(PositionError):
            calling_from(PLAIN_BOB_MAJOR, ["Sideways"])


class TestPositionsIn:
    def test_it_reads_a_calling_back(self):
        assert positions_in(PLAIN_BOB_MAJOR, "pppppp-") == ["Home"]

    def test_it_reads_two_courses_back(self):
        calling = calling_from(PLAIN_BOB_MAJOR, ["Wrong", "Home", "Home"])
        assert positions_in(PLAIN_BOB_MAJOR, calling) == ["Wrong", "Home", "Home"]

    def test_a_plain_course_has_no_positions(self):
        assert positions_in(PLAIN_BOB_MAJOR, "ppppppp") == []

    def test_it_goes_round_trip_at_minor(self):
        calling = calling_from(PLAIN_BOB_MINOR, ["Wrong", "Home"])
        assert positions_in(PLAIN_BOB_MINOR, calling) == ["Wrong", "Home"]

    def test_an_empty_calling_reads_as_nothing(self):
        assert positions_in(PLAIN_BOB_MAJOR, "") == []
