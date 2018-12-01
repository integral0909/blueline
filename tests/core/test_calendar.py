"""The ringing year."""

from __future__ import annotations

from datetime import date

import pytest

from blueline.core.calendar import (
    SUNDAY,
    THURSDAY,
    TUESDAY,
    CalendarError,
    Occasion,
    clashes,
    easter,
    nth_weekday,
    occasions,
    practice_nights,
    sundays,
)


class TestEaster:
    @pytest.mark.parametrize(
        ("year", "when"),
        [
            (2023, date(2023, 4, 9)),
            (2024, date(2024, 3, 31)),
            (2025, date(2025, 4, 20)),
            (2000, date(2000, 4, 23)),
            (1961, date(1961, 4, 2)),
        ],
    )
    def test_known_years(self, year, when) -> None:
        assert easter(year) == when

    def test_it_is_always_a_sunday(self) -> None:
        assert all(easter(year).weekday() == SUNDAY for year in range(1990, 2050))

    def test_it_is_always_in_march_or_april(self) -> None:
        assert all(easter(year).month in {3, 4} for year in range(1990, 2050))

    def test_before_the_gregorian_calendar(self) -> None:
        with pytest.raises(CalendarError, match="1583"):
            easter(1500)


class TestNthWeekday:
    def test_the_first_sunday(self) -> None:
        assert nth_weekday(2023, 1, SUNDAY, 1) == date(2023, 1, 1)

    def test_the_second_sunday(self) -> None:
        assert nth_weekday(2023, 11, SUNDAY, 2) == date(2023, 11, 12)

    def test_the_last_one_counts_back(self) -> None:
        assert nth_weekday(2023, 10, SUNDAY, -1) == date(2023, 10, 29)

    def test_the_second_from_last(self) -> None:
        assert nth_weekday(2023, 10, SUNDAY, -2) == date(2023, 10, 22)

    def test_a_fifth_that_does_not_exist(self) -> None:
        with pytest.raises(CalendarError, match="no 5th"):
            nth_weekday(2023, 2, TUESDAY, 5)

    def test_a_month_that_does_not_exist(self) -> None:
        with pytest.raises(CalendarError, match="no month"):
            nth_weekday(2023, 13, SUNDAY)

    def test_counting_from_zero(self) -> None:
        with pytest.raises(CalendarError, match="counted from one"):
            nth_weekday(2023, 1, SUNDAY, 0)

    def test_december_does_not_run_into_next_year(self) -> None:
        assert nth_weekday(2023, 12, SUNDAY, -1) == date(2023, 12, 31)


class TestOccasions:
    def test_they_come_in_date_order(self) -> None:
        found = [occasion.when for occasion in occasions(2023)]
        assert found == sorted(found)

    def test_christmas_is_there(self) -> None:
        assert any(occasion.name == "Christmas Day" for occasion in occasions(2023))

    def test_easter_moves_with_the_year(self) -> None:
        for year in (2023, 2024):
            found = next(o for o in occasions(year) if o.name == "Easter Sunday")
            assert found.when == easter(year)

    def test_ash_wednesday_is_forty_six_days_before_easter(self) -> None:
        found = next(o for o in occasions(2023) if o.name == "Ash Wednesday")
        assert (easter(2023) - found.when).days == 46

    def test_good_friday_is_not_one(self) -> None:
        # The bells are silent from Maundy Thursday until Easter.
        assert not any(o.name == "Good Friday" for o in occasions(2023))

    def test_remembrance_is_the_second_sunday_in_november(self) -> None:
        found = next(o for o in occasions(2023) if o.name == "Remembrance Sunday")
        assert found.when == date(2023, 11, 12)

    def test_some_are_worth_a_quarter(self) -> None:
        assert any(occasion.worth_a_quarter for occasion in occasions(2023))

    def test_not_all_of_them_are(self) -> None:
        assert not all(occasion.worth_a_quarter for occasion in occasions(2023))

    def test_one_reads_as_a_date(self) -> None:
        assert str(Occasion("Christmas Day", date(2023, 12, 25))) == (
            "Christmas Day, 25 December 2023"
        )


class TestSundays:
    def test_it_finds_them(self) -> None:
        found = sundays(date(2023, 1, 1), date(2023, 1, 31))
        assert found == [
            date(2023, 1, 1),
            date(2023, 1, 8),
            date(2023, 1, 15),
            date(2023, 1, 22),
            date(2023, 1, 29),
        ]

    def test_both_ends_are_included(self) -> None:
        assert sundays(date(2023, 1, 1), date(2023, 1, 1)) == [date(2023, 1, 1)]

    def test_a_range_with_no_sunday_in_it(self) -> None:
        assert sundays(date(2023, 1, 2), date(2023, 1, 5)) == []

    def test_a_range_the_wrong_way_round(self) -> None:
        with pytest.raises(CalendarError, match="before the first"):
            sundays(date(2023, 2, 1), date(2023, 1, 1))


class TestPracticeNights:
    def test_tuesday_by_default(self) -> None:
        found = practice_nights(date(2023, 1, 1), date(2023, 1, 31))
        assert all(when.weekday() == TUESDAY for when in found)

    def test_another_night_can_be_asked_for(self) -> None:
        found = practice_nights(date(2023, 1, 1), date(2023, 1, 31), THURSDAY)
        assert all(when.weekday() == THURSDAY for when in found)

    def test_a_month_has_four_or_five(self) -> None:
        assert len(practice_nights(date(2023, 1, 1), date(2023, 1, 31))) in {4, 5}

    def test_a_day_that_does_not_exist(self) -> None:
        with pytest.raises(CalendarError, match="no day"):
            practice_nights(date(2023, 1, 1), date(2023, 1, 31), 9)

    def test_a_range_the_wrong_way_round(self) -> None:
        with pytest.raises(CalendarError, match="before the first"):
            practice_nights(date(2023, 2, 1), date(2023, 1, 1))


class TestClashes:
    def test_a_practice_on_ash_wednesday(self) -> None:
        nights = practice_nights(date(2023, 1, 1), date(2023, 12, 31), 2)
        assert any(occasion.name == "Ash Wednesday" for occasion in clashes(nights, 2023))

    def test_a_year_with_no_clash(self) -> None:
        assert clashes([date(2023, 6, 6)], 2023) == []

    def test_nothing_planned_clashes_with_nothing(self) -> None:
        assert clashes([], 2023) == []
