import pytest

from blueline.core.calls import plain_bob_calls
from blueline.core.music import count_music
from blueline.core.peals import PEAL, QUARTER, TOUCH, standing_of
from blueline.core.row import Row
from blueline.core.touch import parse_calling, plain_course, repeat
from blueline.service.reports import MAX_REPEATS, Outcome, outcome_of
from tests.methods import PLAIN_BOB_DOUBLES, PLAIN_BOB_MINOR


def an_outcome(**over) -> Outcome:
    """An outcome with everything filled in, for testing the wording.

    Built by hand rather than by ringing something, because the wording has to
    be checked at lengths no method in the set happens to produce.
    """
    fields = {
        "leads": 1,
        "length": 10,
        "comes_round": True,
        "is_true": True,
        "repeats": (),
        "music": count_music([]),
        "final_row": "123456",
        "standing": standing_of(10, 6),
        "early_rounds": None,
        "stands_at_a_lead_end": True,
    }
    fields.update(over)
    return Outcome(**fields)


PB5 = plain_bob_calls(5)
PB6 = plain_bob_calls(6)


class TestOutcomeOf:
    def test_it_leaves_the_closing_row_out_of_the_length(self):
        touch = plain_course(PLAIN_BOB_MINOR)
        assert outcome_of(touch.rows(), touch.leads).length == 60

    def test_a_plain_course_comes_round_and_is_true(self):
        touch = plain_course(PLAIN_BOB_MINOR)
        outcome = outcome_of(touch.rows(), touch.leads)
        assert outcome.comes_round
        assert outcome.is_true
        assert outcome.is_ringable

    def test_the_closing_rounds_is_not_counted_as_a_repeat(self):
        touch = plain_course(PLAIN_BOB_MINOR)
        assert outcome_of(touch.rows(), touch.leads).repeats == ()

    def test_it_says_where_the_touch_finished(self):
        touch = parse_calling(PLAIN_BOB_MINOR, PB6, "--")
        outcome = outcome_of(touch.rows(), touch.leads)
        assert not outcome.comes_round
        assert outcome.final_row != "123456"

    def test_it_counts_the_music(self):
        touch = plain_course(PLAIN_BOB_MINOR)
        assert outcome_of(touch.rows(), touch.leads).music.named["backrounds"] == 1

    def test_it_carries_the_lead_count_through(self):
        touch = parse_calling(PLAIN_BOB_MINOR, PB6, "---")
        assert outcome_of(touch.rows(), touch.leads).leads == 3

    def test_a_false_touch_lists_its_repeats(self):
        touch = repeat(plain_course(PLAIN_BOB_MINOR), 2)
        outcome = outcome_of(touch.rows(), touch.leads)
        assert not outcome.is_true
        assert outcome.repeats

    def test_it_caps_how_many_repeats_it_lists(self):
        touch = repeat(plain_course(PLAIN_BOB_MINOR), 2)
        assert len(outcome_of(touch.rows(), touch.leads).repeats) == MAX_REPEATS

    def test_it_refuses_nothing_at_all(self):
        with pytest.raises(ValueError, match="nothing to report"):
            outcome_of([], 0)

    def test_a_single_row_is_a_touch_of_no_length(self):
        outcome = outcome_of([Row.rounds(6)], 0)
        assert outcome.length == 0
        assert outcome.comes_round


class TestSummarise:
    def _outcome(self, calling: str, method=PLAIN_BOB_MINOR, calls=None):
        touch = parse_calling(method, calls or PB6, calling)
        return outcome_of(touch.rows(), touch.leads)

    def test_a_true_touch_reads_as_true(self):
        assert self._outcome("---").summarise() == "36 true changes"

    def test_it_can_say_what_it_was_of(self):
        assert self._outcome("---").summarise("4 methods") == "36 true changes of 4 methods"

    def test_one_that_does_not_come_round_says_so(self):
        assert "does not come round" in self._outcome("--").summarise()

    def test_a_false_one_says_how_many_rows_repeat(self):
        # Built by hand. Ringing a course twice is false and also comes round
        # early, and early rounds is reported ahead of falseness.
        made = an_outcome(is_true=False, repeats=(), length=120)
        assert "false in 0 rows" in made.summarise()

    def test_early_rounds_is_reported_ahead_of_falseness(self):
        touch = repeat(plain_course(PLAIN_BOB_DOUBLES), 2)
        outcome = outcome_of(touch.rows(), touch.leads)
        assert not outcome.is_true
        assert "comes round early" in outcome.summarise()

    def test_one_repeated_row_reads_as_singular(self):
        made = an_outcome(is_true=False)
        assert "0 rows" in made.summarise()

    def test_the_what_it_was_of_appears_before_the_verdict(self):
        assert self._outcome("--").summarise("2 methods").startswith("24 changes of 2 methods")


class TestStanding:
    def test_a_plain_course_is_only_a_touch(self):
        touch = plain_course(PLAIN_BOB_MINOR)
        assert outcome_of(touch.rows(), touch.leads).standing.counts_as == TOUCH

    def test_the_stage_comes_off_the_rows(self):
        touch = plain_course(PLAIN_BOB_MINOR)
        outcome = outcome_of(touch.rows(), touch.leads)
        assert outcome.standing.length == 60

    def test_a_stage_can_be_given_instead(self):
        touch = plain_course(PLAIN_BOB_MINOR)
        outcome = outcome_of(touch.rows(), touch.leads, stage=8)
        assert outcome.standing.short_by == 1250 - 60

    def test_a_quarter_length_is_named_in_the_summary(self):
        made = an_outcome(length=1260, standing=standing_of(1260, 7))
        assert made.standing.counts_as == QUARTER
        assert "a quarter peal" in made.summarise()

    def test_a_peal_length_is_named_too(self):
        made = an_outcome(length=5040, standing=standing_of(5040, 7))
        assert made.standing.counts_as == PEAL
        assert "a peal" in made.summarise()

    def test_a_short_touch_says_nothing_extra(self):
        touch = plain_course(PLAIN_BOB_MINOR)
        assert outcome_of(touch.rows(), touch.leads).summarise() == "60 true changes"


class TestEarlyRounds:
    def test_a_plain_course_does_not_come_round_early(self):
        touch = plain_course(PLAIN_BOB_MINOR)
        outcome = outcome_of(touch.rows(), touch.leads)
        assert outcome.early_rounds is None

    def test_ringing_a_course_twice_does(self):
        touch = repeat(plain_course(PLAIN_BOB_MINOR), 2)
        outcome = outcome_of(touch.rows(), touch.leads)
        assert outcome.early_rounds is not None
        assert outcome.early_rounds.row == 60

    def test_the_summary_says_so_before_anything_else(self):
        touch = repeat(plain_course(PLAIN_BOB_MINOR), 2)
        outcome = outcome_of(touch.rows(), touch.leads)
        assert "comes round early" in outcome.summarise()

    def test_a_plain_course_stands_at_a_lead_end(self):
        touch = plain_course(PLAIN_BOB_MINOR)
        assert outcome_of(touch.rows(), touch.leads).stands_at_a_lead_end

    def test_a_lead_length_can_be_given(self):
        touch = plain_course(PLAIN_BOB_MINOR)
        outcome = outcome_of(touch.rows(), touch.leads, lead_length=12)
        assert outcome.stands_at_a_lead_end
