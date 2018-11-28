"""Ranking touches by how much of them is worth hearing."""

from __future__ import annotations

from typing import List, Tuple

from collections import Counter

from blueline.core.music import MusicCount, count_music
from blueline.core.scoring import (
    BACK_RUN_WORTH,
    FRONT_RUN_WORTH,
    NAMED_WORTH,
    OTHER_NAMED,
    Score,
    best_of,
    score_music,
    score_rows,
)
from blueline.core.touch import plain_course
from tests.methods import CAMBRIDGE_MINOR, PLAIN_BOB_MAJOR, PLAIN_BOB_MINOR


def music(named=None, back=None, front=None) -> MusicCount:
    return MusicCount(
        named=Counter(named or {}),
        runs_at_back=Counter(back or {}),
        runs_at_front=Counter(front or {}),
    )


class TestScoring:
    def test_nothing_scores_nothing(self) -> None:
        assert score_music(music(), rows=100).total == 0.0

    def test_queens_is_worth_something(self) -> None:
        assert score_music(music(named={"queens": 1}), rows=100).named == NAMED_WORTH["queens"]

    def test_rounds_in_the_middle_is_worth_nothing(self) -> None:
        # It is the touch coming round early, not music, and the proving
        # catches it.
        assert score_music(music(named={"rounds": 3}), rows=100).named == 0.0

    def test_something_named_it_has_no_opinion_about(self) -> None:
        assert score_music(music(named={"whittingtons": 1}), rows=100).named == OTHER_NAMED

    def test_a_run_off_the_back_counts(self) -> None:
        assert score_music(music(back={4: 2}), rows=100).back == 2 * BACK_RUN_WORTH[4]

    def test_a_longer_run_is_worth_more(self) -> None:
        assert BACK_RUN_WORTH[6] > BACK_RUN_WORTH[4]

    def test_the_back_beats_the_front(self) -> None:
        assert BACK_RUN_WORTH[5] > FRONT_RUN_WORTH[5]

    def test_a_run_longer_than_the_table_still_counts(self) -> None:
        # Ten bell methods have runs this table has never heard of.
        assert score_music(music(back={10: 1}), rows=100).back == max(BACK_RUN_WORTH.values())

    def test_the_total_adds_the_three_up(self) -> None:
        scored = score_music(music(named={"queens": 1}, back={4: 1}, front={4: 1}), rows=10)
        assert scored.total == scored.named + scored.back + scored.front


class TestPerRow:
    def test_it_divides_by_the_rows(self) -> None:
        scored = Score(rows=10, named=10.0, back=0.0, front=0.0)
        assert scored.per_row == 1.0

    def test_nothing_rung_scores_nothing(self) -> None:
        assert Score(rows=0, named=5.0, back=0.0, front=0.0).per_row == 0.0

    def test_length_alone_is_not_an_advantage(self) -> None:
        short = Score(rows=100, named=10.0, back=0.0, front=0.0)
        long = Score(rows=1000, named=100.0, back=0.0, front=0.0)
        assert short.per_row == long.per_row

    def test_it_reads_as_a_score(self) -> None:
        assert str(Score(rows=10, named=4.0, back=0.0, front=0.0)) == "4 over 10 rows"

    def test_a_summary_says_where_it_came_from(self) -> None:
        scored = Score(rows=10, named=4.0, back=2.0, front=0.0)
        assert "off the back" in scored.summary()

    def test_a_summary_of_nothing(self) -> None:
        assert Score(rows=10, named=0.0, back=0.0, front=0.0).summary() == "nothing much"


class TestRealCourses:
    def test_a_plain_course_scores_something(self) -> None:
        rows = plain_course(PLAIN_BOB_MAJOR).rows()
        assert score_rows(rows).total > 0

    def test_major_has_more_music_than_minor(self) -> None:
        # More bells behind the treble means more room for runs.
        major = score_rows(plain_course(PLAIN_BOB_MAJOR).rows()).per_row
        minor = score_rows(plain_course(PLAIN_BOB_MINOR).rows()).per_row
        assert major > minor

    def test_it_counts_the_rows_it_was_given(self) -> None:
        rows = plain_course(CAMBRIDGE_MINOR).rows()
        assert score_rows(rows).rows == len(rows)

    def test_scoring_counted_music_and_scoring_rows_agree(self) -> None:
        rows = plain_course(CAMBRIDGE_MINOR).rows()
        assert score_rows(rows) == score_music(count_music(rows), len(rows))

    def test_a_higher_minimum_run_finds_less(self) -> None:
        rows = plain_course(PLAIN_BOB_MAJOR).rows()
        assert score_rows(rows, min_run=6).total <= score_rows(rows, min_run=4).total


class TestBestOf:
    def entries(self) -> List[Tuple[str, Score]]:
        return [
            ("--", Score(rows=100, named=10.0, back=0.0, front=0.0)),
            ("-s-", Score(rows=100, named=30.0, back=0.0, front=0.0)),
            ("s-s", Score(rows=100, named=20.0, back=0.0, front=0.0)),
        ]

    def test_the_most_musical_comes_first(self) -> None:
        assert best_of(self.entries())[0][0] == "-s-"

    def test_it_can_be_cut_short(self) -> None:
        assert len(best_of(self.entries(), how_many=2)) == 2

    def test_a_short_touch_beats_a_long_dull_one(self) -> None:
        entries = [
            ("short", Score(rows=100, named=50.0, back=0.0, front=0.0)),
            ("long", Score(rows=5000, named=100.0, back=0.0, front=0.0)),
        ]
        assert best_of(entries)[0][0] == "short"

    def test_a_tie_puts_the_longer_first(self) -> None:
        entries = [
            ("short", Score(rows=100, named=10.0, back=0.0, front=0.0)),
            ("long", Score(rows=200, named=20.0, back=0.0, front=0.0)),
        ]
        assert best_of(entries)[0][0] == "long"

    def test_nothing_to_rank(self) -> None:
        assert best_of([]) == []
