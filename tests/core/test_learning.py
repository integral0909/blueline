"""What to learn next, and in what order."""

from __future__ import annotations

from blueline.analysis import analyse
from blueline.core.learning import (
    Difficulty,
    difficulty_of,
    dodges_in,
    in_order,
    next_after,
    places_in,
    step_up,
)
from blueline.library.builtin import standard_methods
from tests.methods import (
    CAMBRIDGE_MAJOR,
    CAMBRIDGE_MINOR,
    GRANDSIRE_DOUBLES,
    PLAIN_BOB_DOUBLES,
    PLAIN_BOB_MAJOR,
    PLAIN_BOB_MINOR,
)


def hardness(method) -> Difficulty:
    return difficulty_of(analyse(method), method)


EVERYTHING = [hardness(method) for method in standard_methods()]


class TestCounting:
    def test_plain_bob_does_no_dodging_inside_a_lead(self) -> None:
        # The dodging in Plain Bob happens at the lead end, which is the
        # closing row and belongs to the next lead.
        assert dodges_in(PLAIN_BOB_MINOR) == 0

    def test_a_surprise_method_dodges_more(self) -> None:
        assert dodges_in(CAMBRIDGE_MINOR) > dodges_in(PLAIN_BOB_MINOR)

    def test_plain_bob_makes_places(self) -> None:
        assert places_in(PLAIN_BOB_MINOR) > 0

    def test_a_surprise_method_makes_more(self) -> None:
        assert places_in(CAMBRIDGE_MINOR) > places_in(PLAIN_BOB_MINOR)

    def test_counting_is_the_same_at_any_stage(self) -> None:
        assert dodges_in(PLAIN_BOB_MAJOR) >= dodges_in(PLAIN_BOB_MINOR)


class TestDifficulty:
    def test_the_easiest_thing_anybody_learns(self) -> None:
        easiest = in_order(EVERYTHING)[0]
        assert easiest.title == "Plain Bob Doubles"

    def test_a_bigger_stage_is_harder(self) -> None:
        assert hardness(PLAIN_BOB_MAJOR).score > hardness(PLAIN_BOB_MINOR).score

    def test_grandsire_is_harder_than_plain_bob(self) -> None:
        # Two hunt bells rather than one, which is the whole reason a band
        # teaches them in that order.
        assert hardness(GRANDSIRE_DOUBLES).score > hardness(PLAIN_BOB_DOUBLES).score

    def test_surprise_is_harder_than_plain(self) -> None:
        assert hardness(CAMBRIDGE_MINOR).score > hardness(PLAIN_BOB_MINOR).score

    def test_it_says_why(self) -> None:
        assert hardness(GRANDSIRE_DOUBLES).reasons

    def test_two_hunt_bells_is_one_of_the_reasons(self) -> None:
        assert any("hunt bells" in reason for reason in hardness(GRANDSIRE_DOUBLES).reasons)

    def test_a_plain_method_needs_little_explaining(self) -> None:
        assert len(hardness(PLAIN_BOB_DOUBLES).reasons) <= 2

    def test_it_reads_as_a_score(self) -> None:
        assert str(hardness(PLAIN_BOB_MINOR)).startswith("Plain Bob Minor: ")


class TestBands:
    def test_plain_bob_doubles_is_a_learners_method(self) -> None:
        assert hardness(PLAIN_BOB_DOUBLES).band == "learner"

    def test_surprise_major_is_advanced(self) -> None:
        assert hardness(CAMBRIDGE_MAJOR).band == "advanced"

    def test_the_bands_climb_with_the_score(self) -> None:
        order = ["learner", "improver", "competent", "advanced"]
        seen = [order.index(each.band) for each in in_order(EVERYTHING)]
        assert seen == sorted(seen)

    def test_every_band_is_one_of_four(self) -> None:
        assert {each.band for each in EVERYTHING} <= {
            "learner",
            "improver",
            "competent",
            "advanced",
        }


class TestOrder:
    def test_easiest_first(self) -> None:
        scores = [each.score for each in in_order(EVERYTHING)]
        assert scores == sorted(scores)

    def test_a_tie_goes_by_stage(self) -> None:
        made = [
            Difficulty("B Major", 8, 40.0, ()),
            Difficulty("A Minor", 6, 40.0, ()),
        ]
        assert [each.title for each in in_order(made)] == ["A Minor", "B Major"]

    def test_it_puts_the_standard_progression_in_the_usual_order(self) -> None:
        titles = [each.title for each in in_order(EVERYTHING)]
        assert titles.index("Plain Bob Doubles") < titles.index("Grandsire Doubles")
        assert titles.index("Grandsire Doubles") < titles.index("Cambridge Surprise Minor")


class TestWhatNext:
    def test_it_suggests_the_easiest_thing_unknown(self) -> None:
        suggested = next_after(EVERYTHING, known=set())
        assert suggested[0].title == "Plain Bob Doubles"

    def test_it_skips_what_somebody_already_rings(self) -> None:
        suggested = next_after(EVERYTHING, known={"Plain Bob Doubles"})
        assert suggested[0].title != "Plain Bob Doubles"

    def test_names_are_not_case_sensitive(self) -> None:
        suggested = next_after(EVERYTHING, known={"  plain bob doubles "})
        assert suggested[0].title != "Plain Bob Doubles"

    def test_it_gives_as_many_as_asked_for(self) -> None:
        assert len(next_after(EVERYTHING, known=set(), how_many=5)) == 5

    def test_somebody_who_rings_everything_gets_nothing(self) -> None:
        known = {each.title for each in EVERYTHING}
        assert next_after(EVERYTHING, known) == []

    def test_it_fills_gaps_behind_somebody(self) -> None:
        # Learnt Cambridge out of order. The gap behind is better advice.
        suggested = next_after(EVERYTHING, known={"Cambridge Surprise Minor"})
        assert suggested[0].title == "Plain Bob Doubles"


class TestStepUp:
    def test_it_looks_past_what_somebody_rings(self) -> None:
        known = {"Cambridge Surprise Minor"}
        cambridge = next(each for each in EVERYTHING if each.title in known)
        step = step_up(EVERYTHING, known)
        assert step is not None
        assert step.score > cambridge.score

    def test_somebody_starting_out(self) -> None:
        step = step_up(EVERYTHING, known=set())
        assert step is not None
        assert step.title == "Plain Bob Doubles"

    def test_somebody_who_rings_everything(self) -> None:
        known = {each.title for each in EVERYTHING}
        assert step_up(EVERYTHING, known) is None

    def test_it_differs_from_filling_a_gap(self) -> None:
        known = {"Cambridge Surprise Minor"}
        assert step_up(EVERYTHING, known) != next_after(EVERYTHING, known)[0]
