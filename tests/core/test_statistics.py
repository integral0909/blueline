from collections import Counter
from datetime import date

from blueline.core.bands import band_of
from blueline.core.performance import Performance
from blueline.core.statistics import Totals, leaderboard, totals_of

EIGHT = ["Ann", "Bob", "Cara", "Dan", "Eve", "Finn", "Gus", "Hana"]
OTHER = ["Ann", "Ivy", "Jed", "Kit", "Lex", "Mo", "Nell", "Opal"]


def a_performance(**over) -> Performance:
    fields = {
        "band": band_of(EIGHT, conductor="Hana"),
        "title": "Cambridge Surprise Major",
        "stage": 8,
        "length": 5024,
        "rang_on": date(2023, 3, 18),
        "place": "St Andrew, Marchgate",
        "composer": None,
    }
    fields.update(over)
    return Performance(**fields)


SOME = [
    a_performance(),
    a_performance(
        title="Yorkshire Surprise Major",
        length=1250,
        rang_on=date(2023, 4, 2),
        place="St Mary, Ashcombe",
        band=band_of(OTHER),
    ),
    a_performance(title="Cambridge Surprise Major", length=224, rang_on=date(2023, 1, 5)),
]


class TestEmpty:
    def test_nothing_adds_up_to_nothing(self):
        totals = totals_of([])
        assert totals.performances == 0
        assert totals.changes == 0
        assert totals.peals == 0

    def test_it_says_so(self):
        assert totals_of([]).summary() == "nothing rung"

    def test_there_are_no_dates(self):
        totals = totals_of([])
        assert totals.first is None
        assert totals.last is None

    def test_there_is_no_commonest_anything(self):
        totals = totals_of([])
        assert totals.most_rung_method() is None
        assert totals.busiest_place() is None
        assert totals.busiest_ringer() is None

    def test_the_average_of_nothing_is_nothing(self):
        assert totals_of([]).average_length == 0


class TestCounting:
    def test_it_counts_the_performances(self):
        assert totals_of(SOME).performances == 3

    def test_it_totals_the_changes(self):
        assert totals_of(SOME).changes == 5024 + 1250 + 224

    def test_it_counts_the_peals(self):
        assert totals_of(SOME).peals == 1

    def test_it_counts_the_quarters(self):
        assert totals_of(SOME).quarters == 1

    def test_everything_else_is_a_touch(self):
        assert totals_of(SOME).touches == 1

    def test_the_three_add_up_to_the_whole(self):
        totals = totals_of(SOME)
        assert totals.peals + totals.quarters + totals.touches == totals.performances

    def test_it_counts_the_places(self):
        assert totals_of(SOME).places == 2

    def test_it_counts_the_ringers(self):
        # Ann rang in both bands and is one person.
        assert totals_of(SOME).ringers == 15

    def test_it_works_out_the_average(self):
        assert totals_of(SOME).average_length == (5024 + 1250 + 224) // 3


class TestDates:
    def test_it_finds_the_first(self):
        assert totals_of(SOME).first == date(2023, 1, 5)

    def test_it_finds_the_last(self):
        assert totals_of(SOME).last == date(2023, 4, 2)

    def test_one_performance_is_both(self):
        totals = totals_of([a_performance()])
        assert totals.first == totals.last


class TestBreakdowns:
    def test_it_counts_by_method(self):
        assert totals_of(SOME).by_method["Cambridge Surprise Major"] == 2

    def test_it_counts_by_place(self):
        assert totals_of(SOME).by_place["St Andrew, Marchgate"] == 2

    def test_it_counts_by_ringer(self):
        assert totals_of(SOME).by_ringer["Ann"] == 3

    def test_a_ringer_in_one_band_is_counted_once(self):
        assert totals_of(SOME).by_ringer["Ivy"] == 1

    def test_it_counts_by_stage(self):
        assert totals_of(SOME).by_stage[8] == 3

    def test_the_commonest_method(self):
        assert totals_of(SOME).most_rung_method() == ("Cambridge Surprise Major", 2)

    def test_the_busiest_place(self):
        assert totals_of(SOME).busiest_place() == ("St Andrew, Marchgate", 2)

    def test_the_busiest_ringer(self):
        assert totals_of(SOME).busiest_ringer() == ("Ann", 3)

    def test_a_tie_is_broken_the_same_way_every_time(self):
        # most_common alone gives whichever the dictionary saw first, which
        # makes a report that changes between runs for no reason.
        counted = Counter({"Zoe": 2, "Ann": 2})
        totals = Totals(
            performances=0,
            peals=0,
            quarters=0,
            changes=0,
            places=0,
            ringers=0,
            first=None,
            last=None,
            by_ringer=counted,
        )
        assert totals.busiest_ringer() == ("Ann", 2)


class TestLeaderboard:
    def test_the_most_comes_first(self):
        board = leaderboard(Counter({"Ann": 3, "Bob": 1, "Cara": 2}))
        assert [name for name, _ in board] == ["Ann", "Cara", "Bob"]

    def test_a_tie_is_broken_alphabetically(self):
        board = leaderboard(Counter({"Zoe": 2, "Ann": 2}))
        assert [name for name, _ in board] == ["Ann", "Zoe"]

    def test_it_can_be_capped(self):
        assert len(leaderboard(Counter({"a": 3, "b": 2, "c": 1}), top=2)) == 2

    def test_an_empty_counter_gives_an_empty_board(self):
        assert leaderboard(Counter()) == []


class TestSummary:
    def test_it_names_the_totals(self):
        summary = totals_of(SOME).summary()
        assert "3 performances" in summary
        assert "1 peals" in summary

    def test_it_leaves_out_what_there_is_none_of(self):
        only_touches = totals_of([a_performance(length=224)])
        assert "peals" not in only_touches.summary()
