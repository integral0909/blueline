import pytest

from blueline.core.calls import grandsire_calls, plain_bob_calls
from blueline.core.row import Row
from blueline.core.touch import (
    Touch,
    TouchError,
    extent_length,
    is_extent,
    parse_calling,
    plain_course,
    repeat,
)
from tests.methods import (
    CAMBRIDGE_MINOR,
    GRANDSIRE_DOUBLES,
    PLAIN_BOB_DOUBLES,
    PLAIN_BOB_MAJOR,
    PLAIN_BOB_MINOR,
)

PB5 = plain_bob_calls(5)
PB6 = plain_bob_calls(6)
PB8 = plain_bob_calls(8)


class TestPlainCourse:
    def test_minor_plain_course_is_sixty_changes(self):
        assert plain_course(PLAIN_BOB_MINOR).length == 60

    def test_major_plain_course_is_a_hundred_and_twelve(self):
        assert plain_course(PLAIN_BOB_MAJOR).length == 112

    def test_cambridge_plain_course_is_a_hundred_and_twenty(self):
        assert plain_course(CAMBRIDGE_MINOR).length == 120

    def test_a_plain_course_comes_round(self):
        assert plain_course(PLAIN_BOB_MINOR).comes_round()

    def test_a_plain_course_is_true(self):
        assert plain_course(CAMBRIDGE_MINOR).is_true()

    def test_it_is_all_plain_leads(self):
        assert plain_course(PLAIN_BOB_MINOR).calling == "ppppp"

    def test_there_is_one_more_row_than_the_touch_is_long(self):
        touch = plain_course(PLAIN_BOB_MINOR)
        assert len(touch.rows()) == touch.length + 1

    def test_it_opens_on_rounds(self):
        assert plain_course(PLAIN_BOB_MINOR).rows()[0].is_rounds


class TestCalling:
    def test_reads_a_calling_off_a_string(self):
        touch = parse_calling(PLAIN_BOB_MINOR, PB6, "-p-s")
        assert touch.leads == 4
        assert touch.calling == "-p-s"

    def test_ignores_spaces_in_a_calling(self):
        assert parse_calling(PLAIN_BOB_MINOR, PB6, "- - -").calling == "---"

    def test_refuses_a_symbol_it_does_not_know(self):
        with pytest.raises(TouchError):
            parse_calling(PLAIN_BOB_MINOR, PB6, "-x-")

    def test_refuses_an_empty_calling(self):
        with pytest.raises(TouchError):
            parse_calling(PLAIN_BOB_MINOR, PB6, "   ")

    def test_refuses_a_call_from_the_wrong_stage(self):
        with pytest.raises(TouchError):
            Touch(method=PLAIN_BOB_MINOR, calls=(PB8["-"],))

    def test_refuses_a_start_row_from_the_wrong_stage(self):
        with pytest.raises(TouchError):
            plain_course(PLAIN_BOB_MINOR).rows(Row.rounds(8))


class TestThreeBobTouch:
    def test_it_is_thirty_six_changes(self):
        assert parse_calling(PLAIN_BOB_MINOR, PB6, "---").length == 36

    def test_it_comes_round(self):
        assert parse_calling(PLAIN_BOB_MINOR, PB6, "---").comes_round()

    def test_it_is_true(self):
        assert parse_calling(PLAIN_BOB_MINOR, PB6, "---").is_true()

    def test_two_bobs_do_not_come_round(self):
        assert not parse_calling(PLAIN_BOB_MINOR, PB6, "--").comes_round()


class TestRepeat:
    def test_ringing_a_block_twice_doubles_the_length(self):
        block = parse_calling(PLAIN_BOB_MINOR, PB6, "---")
        assert repeat(block, 2).length == block.length * 2

    def test_the_calling_repeats_too(self):
        block = parse_calling(PLAIN_BOB_MINOR, PB6, "-p")
        assert repeat(block, 3).calling == "-p-p-p"

    def test_ringing_it_once_leaves_it_alone(self):
        block = parse_calling(PLAIN_BOB_MINOR, PB6, "---")
        assert repeat(block, 1).calls == block.calls

    def test_refuses_ringing_a_block_no_times(self):
        with pytest.raises(TouchError):
            repeat(plain_course(PLAIN_BOB_MINOR), 0)


class TestExtents:
    def test_an_extent_of_doubles_is_a_hundred_and_twenty(self):
        assert extent_length(5) == 120

    def test_an_extent_of_minor_is_seven_hundred_and_twenty(self):
        assert extent_length(6) == 720

    def test_an_extent_of_major_is_forty_thousand_odd(self):
        assert extent_length(8) == 40320

    def test_the_classic_hundred_and_twenty_of_plain_bob_doubles(self):
        # Three courses with a bob at the end of each. The first touch most
        # ringers ever call.
        touch = repeat(parse_calling(PLAIN_BOB_DOUBLES, PB5, "ppp-"), 3)
        assert touch.length == 120
        assert touch.comes_round()
        assert touch.is_true()
        assert is_extent(touch)

    def test_it_really_does_ring_every_row(self):
        touch = repeat(parse_calling(PLAIN_BOB_DOUBLES, PB5, "ppp-"), 3)
        assert len(set(touch.rows()[:-1])) == 120

    def test_a_plain_course_is_not_an_extent(self):
        assert not is_extent(plain_course(PLAIN_BOB_DOUBLES))

    def test_something_that_does_not_come_round_is_not_an_extent(self):
        assert not is_extent(parse_calling(PLAIN_BOB_MINOR, PB6, "--"))


class TestGrandsire:
    def test_a_grandsire_plain_course_comes_round(self):
        assert plain_course(GRANDSIRE_DOUBLES).comes_round()

    def test_a_grandsire_plain_course_is_thirty_changes(self):
        assert plain_course(GRANDSIRE_DOUBLES).length == 30

    def test_grandsire_takes_its_own_calls(self):
        touch = parse_calling(GRANDSIRE_DOUBLES, grandsire_calls(5), "-p-")
        assert touch.leads == 3
        assert touch.length == 30
