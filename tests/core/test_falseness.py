from blueline.core.falseness import (
    FalseCourseHead,
    clashes_between,
    course_rows,
    false_course_head_rows,
    false_course_heads,
    head_taking,
    is_true_against,
    tenors_together_heads,
    transposed_course,
)
from blueline.core.row import Row
from tests.methods import CAMBRIDGE_MAJOR, CAMBRIDGE_MINOR, PLAIN_BOB_MINOR


class TestHeadTaking:
    def test_the_head_from_a_row_to_itself_is_rounds(self):
        row = Row.parse("135264")
        assert head_taking(row, row).is_rounds

    def test_it_really_does_take_the_first_to_the_second(self):
        first, second = Row.parse("135264"), Row.parse("142635")
        assert first.transposed_by(head_taking(first, second)) == second

    def test_from_rounds_it_is_just_the_other_row(self):
        second = Row.parse("135264")
        assert head_taking(Row.rounds(6), second) == second


class TestCourseRows:
    def test_it_leaves_the_closing_rounds_off(self):
        rows = course_rows(PLAIN_BOB_MINOR)
        assert len(rows) == 60
        assert sum(1 for row in rows if row.is_rounds) == 1

    def test_a_transposed_course_is_the_same_length(self):
        rows = course_rows(PLAIN_BOB_MINOR)
        moved = transposed_course(rows, Row.parse("134256"))
        assert len(moved) == len(rows)

    def test_transposing_by_rounds_changes_nothing(self):
        rows = course_rows(PLAIN_BOB_MINOR)
        assert transposed_course(rows, Row.rounds(6)) == rows

    def test_it_counts_what_two_courses_share(self):
        rows = course_rows(PLAIN_BOB_MINOR)
        assert clashes_between(rows, rows) == 60

    def test_two_courses_with_nothing_in_common_share_nothing(self):
        assert clashes_between([Row.rounds(6)], [Row.parse("214365")]) == 0


class TestFalseCourseHeads:
    def test_rounds_is_never_reported(self):
        for entry in false_course_heads(PLAIN_BOB_MINOR):
            assert not entry.head.is_rounds

    def test_every_reported_head_really_does_clash(self):
        rows = course_rows(CAMBRIDGE_MINOR)
        original = set(rows)
        for entry in false_course_heads(CAMBRIDGE_MINOR)[:20]:
            shared = sum(1 for row in rows if row.transposed_by(entry.head) in original)
            assert shared == entry.clashes

    def test_a_reported_head_makes_the_pair_false(self):
        entry = false_course_heads(CAMBRIDGE_MINOR)[0]
        assert not is_true_against(CAMBRIDGE_MINOR, [Row.rounds(6), entry.head])

    def test_the_worst_head_comes_first(self):
        found = false_course_heads(CAMBRIDGE_MAJOR)
        assert found[0].clashes >= found[-1].clashes

    def test_they_come_back_in_a_settled_order(self):
        first = [str(entry.head) for entry in false_course_heads(CAMBRIDGE_MINOR)]
        second = [str(entry.head) for entry in false_course_heads(CAMBRIDGE_MINOR)]
        assert first == second

    def test_the_hunt_bell_is_left_alone_by_default(self):
        for entry in false_course_heads(CAMBRIDGE_MAJOR):
            assert entry.head[1] == 1

    def test_asking_for_all_of_them_gives_more(self):
        fixed = false_course_heads(CAMBRIDGE_MINOR)
        everything = false_course_heads(CAMBRIDGE_MINOR, hunt_fixed=False)
        assert len(everything) > len(fixed)

    def test_the_rows_helper_gives_the_same_heads(self):
        entries = false_course_heads(PLAIN_BOB_MINOR)
        assert false_course_head_rows(PLAIN_BOB_MINOR) == [entry.head for entry in entries]

    def test_a_head_reads_as_the_row_and_its_count(self):
        assert str(FalseCourseHead(head=Row.parse("135264"), clashes=20)) == "135264 (20)"


class TestTruthAgainst:
    def test_the_plain_course_on_its_own_is_true(self):
        assert is_true_against(CAMBRIDGE_MINOR, [Row.rounds(6)])

    def test_the_same_course_twice_is_not(self):
        assert not is_true_against(CAMBRIDGE_MINOR, [Row.rounds(6), Row.rounds(6)])

    def test_no_courses_at_all_is_true(self):
        assert is_true_against(CAMBRIDGE_MINOR, [])


class TestTenorsTogether:
    def test_they_all_leave_the_back_two_alone(self):
        stage = CAMBRIDGE_MAJOR.stage
        for head in tenors_together_heads(CAMBRIDGE_MAJOR):
            assert head[stage] == stage
            assert head[stage - 1] == stage - 1

    def test_there_are_fewer_than_the_whole_set(self):
        together = tenors_together_heads(CAMBRIDGE_MAJOR)
        assert len(together) < len(false_course_heads(CAMBRIDGE_MAJOR))

    def test_a_stage_too_small_to_have_tenors_gives_nothing(self):
        from blueline.core.method import Method

        tiny = Method.from_notation("tiny", 3, "3.1.3")
        assert tenors_together_heads(tiny) == []

    def test_the_surprise_major_methods_all_have_some(self):
        assert len(tenors_together_heads(CAMBRIDGE_MAJOR)) > 0
