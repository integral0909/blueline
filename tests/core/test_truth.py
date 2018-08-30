from blueline.core.calls import plain_bob_calls
from blueline.core.row import Row
from blueline.core.touch import parse_calling, plain_course, repeat
from blueline.core.truth import (
    Repeat,
    extent_length,
    is_extent,
    prove,
    prove_against,
    prove_touch,
    rung_rows,
)
from tests.methods import (
    CAMBRIDGE_MAJOR,
    CAMBRIDGE_MINOR,
    PLAIN_BOB_DOUBLES,
    PLAIN_BOB_MAJOR,
    PLAIN_BOB_MINOR,
)

PB5 = plain_bob_calls(5)
PB6 = plain_bob_calls(6)


class TestProve:
    def test_all_different_rows_are_true(self):
        rows = [Row.parse("123456"), Row.parse("214365"), Row.parse("241635")]
        assert prove(rows).is_true

    def test_a_repeat_makes_it_false(self):
        rows = [Row.parse("123456"), Row.parse("214365"), Row.parse("123456")]
        assert not prove(rows).is_true

    def test_it_says_which_row_repeated(self):
        rows = [Row.parse("123456"), Row.parse("214365"), Row.parse("123456")]
        report = prove(rows)
        assert report.rows_repeated == 1
        assert report.repeats[0].row == Row.parse("123456")

    def test_it_says_where(self):
        rows = [Row.parse("123456"), Row.parse("214365"), Row.parse("123456")]
        assert prove(rows).repeats[0].positions == (1, 3)

    def test_positions_count_from_one(self):
        rows = [Row.parse("123456"), Row.parse("123456")]
        assert prove(rows).repeats[0].positions[0] == 1

    def test_it_counts_the_rows(self):
        report = prove([Row.parse("123456"), Row.parse("214365"), Row.parse("123456")])
        assert report.total == 3
        assert report.distinct == 2

    def test_an_empty_run_is_true(self):
        assert prove([]).is_true

    def test_it_finds_a_row_rung_three_times(self):
        rows = [Row.rounds(6)] * 3
        assert prove(rows).repeats[0].times == 3

    def test_the_worst_row_is_the_one_rung_most(self):
        rows = [Row.rounds(6)] * 3 + [Row.parse("214365")] * 2
        assert prove(rows).worst.row == Row.rounds(6)

    def test_there_is_no_worst_row_when_it_is_true(self):
        assert prove([Row.rounds(6)]).worst is None

    def test_repeats_come_back_in_the_order_they_first_appeared(self):
        rows = [Row.parse("214365"), Row.rounds(6), Row.parse("214365"), Row.rounds(6)]
        firsts = [rep.positions[0] for rep in prove(rows).repeats]
        assert firsts == sorted(firsts)


class TestRepeatText:
    def test_it_reads_as_the_row_and_its_places(self):
        text = str(Repeat(row=Row.rounds(6), positions=(1, 30)))
        assert text == "123456 at 1, 30"


class TestSummary:
    def test_a_true_touch_says_how_many_rows(self):
        assert prove([Row.rounds(6)]).summary() == "true, 1 rows"

    def test_a_false_one_says_how_many_repeated(self):
        assert "false" in prove([Row.rounds(6)] * 2).summary()


class TestProveTouch:
    def test_the_closing_rounds_is_not_counted(self):
        touch = plain_course(PLAIN_BOB_MINOR)
        assert len(rung_rows(touch)) == touch.length

    def test_a_plain_course_is_true(self):
        assert prove_touch(plain_course(PLAIN_BOB_MINOR)).is_true

    def test_cambridge_is_true(self):
        assert prove_touch(plain_course(CAMBRIDGE_MINOR)).is_true

    def test_cambridge_major_is_true(self):
        assert prove_touch(plain_course(CAMBRIDGE_MAJOR)).is_true

    def test_major_is_true(self):
        assert prove_touch(plain_course(PLAIN_BOB_MAJOR)).is_true

    def test_the_classic_hundred_and_twenty_is_true(self):
        touch = repeat(parse_calling(PLAIN_BOB_DOUBLES, PB5, "ppp-"), 3)
        report = prove_touch(touch)
        assert report.is_true
        assert report.total == 120
        assert report.distinct == 120

    def test_ringing_a_plain_course_twice_is_false(self):
        touch = repeat(plain_course(PLAIN_BOB_MINOR), 2)
        report = prove_touch(touch)
        assert not report.is_true
        assert report.rows_repeated == 60

    def test_every_row_repeats_exactly_twice(self):
        touch = repeat(plain_course(PLAIN_BOB_MINOR), 2)
        assert all(rep.times == 2 for rep in prove_touch(touch).repeats)


class TestProveAgainst:
    def test_a_block_true_against_nothing(self):
        rows = plain_course(PLAIN_BOB_MINOR).rows()[:-1]
        assert prove_against(rows, []).is_true

    def test_a_block_false_against_itself(self):
        rows = plain_course(PLAIN_BOB_MINOR).rows()[:-1]
        assert not prove_against(rows, rows).is_true

    def test_it_counts_both_lots(self):
        rows = plain_course(PLAIN_BOB_MINOR).rows()[:-1]
        assert prove_against(rows, rows).total == 120


class TestExtentLength:
    def test_doubles(self):
        assert extent_length(5) == 120

    def test_minor(self):
        assert extent_length(6) == 720

    def test_major(self):
        assert extent_length(8) == 40320

    def test_it_is_the_stage_factorial(self):
        assert extent_length(4) == 24

    def test_the_classic_hundred_and_twenty_is_an_extent(self):
        touch = repeat(parse_calling(PLAIN_BOB_DOUBLES, PB5, "ppp-"), 3)
        assert is_extent(touch)

    def test_a_plain_course_is_not(self):
        assert not is_extent(plain_course(PLAIN_BOB_DOUBLES))

    def test_something_false_is_not_an_extent_however_long(self):
        assert not is_extent(repeat(plain_course(PLAIN_BOB_MINOR), 12))
