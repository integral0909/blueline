"""The ringing year.

A tower rings to a calendar and the calendar is not the one a diary keeps. The
fixed points are Sunday service, the practice night, and the days the bells go
for something in particular: Christmas, Easter, Remembrance Sunday, the patronal
festival. A band planning a term works from that, and so does anybody asking
why the tower was silent on the second Tuesday in August.

Easter is worked out rather than looked up. A table would run out, and the sum
is old enough that it is not going to change: this is the anonymous Gregorian
computus, the one every almanac uses.

Nothing here knows about a particular tower. Which Sunday a patronal festival
falls on is a fact about a dedication and belongs with the tower, not here.
"""

from __future__ import annotations

from typing import List

from dataclasses import dataclass
from datetime import date, timedelta

from blueline.errors import BluelineError

MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(7)

DAY_NAMES = {
    MONDAY: "Monday",
    TUESDAY: "Tuesday",
    WEDNESDAY: "Wednesday",
    THURSDAY: "Thursday",
    FRIDAY: "Friday",
    SATURDAY: "Saturday",
    SUNDAY: "Sunday",
}


class CalendarError(BluelineError):
    """A date this cannot work with."""


def easter(year: int) -> date:
    """Easter Sunday, by the anonymous Gregorian computus."""
    if year < 1583:
        raise CalendarError("the Gregorian calendar starts in 1583")
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    lunar = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 19 * lunar) // 433
    month = (h + lunar - 7 * m + 90) // 25
    day = (h + lunar - 7 * m + 33 * month + 19) % 32
    return date(year, month, day)


def nth_weekday(year: int, month: int, weekday: int, which: int = 1) -> date:
    """The nth given weekday of a month, counting from one.

    A negative which counts back from the end, so -1 is the last one, which is
    how anybody says it: the last Sunday in October.
    """
    if not 1 <= month <= 12:
        raise CalendarError(f"there is no month {month}")
    if which == 0:
        raise CalendarError("weekdays in a month are counted from one")

    if which > 0:
        first = date(year, month, 1)
        ahead = (weekday - first.weekday()) % 7
        found = first + timedelta(days=ahead + 7 * (which - 1))
        if found.month != month:
            raise CalendarError(f"there is no {which}th of that day in {year}-{month:02d}")
        return found

    last_day = (date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1)).day
    last = date(year, month, last_day)
    back = (last.weekday() - weekday) % 7
    return last - timedelta(days=back + 7 * (-which - 1))


@dataclass(frozen=True)
class Occasion:
    """A day the bells go for something in particular."""

    name: str
    when: date
    #: Whether a band would expect to ring a quarter for it rather than just
    #: the usual service touch.
    worth_a_quarter: bool = False

    def __str__(self) -> str:
        return f"{self.name}, {self.when:%d %B %Y}"


def occasions(year: int) -> List[Occasion]:
    """The days the bells go for a reason, in date order.

    The fixed feasts and the ones that move with Easter. Not a complete church
    calendar: these are the ones a tower actually rings for, which is a much
    shorter list than the one in the prayer book.
    """
    easter_day = easter(year)
    found = [
        Occasion("New Year", date(year, 1, 1)),
        Occasion("Ash Wednesday", easter_day - timedelta(days=46)),
        Occasion("Palm Sunday", easter_day - timedelta(days=7)),
        # Bells are traditionally silent from Maundy Thursday until Easter,
        # which is why Good Friday is not in this list.
        Occasion("Easter Sunday", easter_day, worth_a_quarter=True),
        Occasion("Ascension Day", easter_day + timedelta(days=39)),
        Occasion("Whit Sunday", easter_day + timedelta(days=49), worth_a_quarter=True),
        Occasion("Remembrance Sunday", nth_weekday(year, 11, SUNDAY, 2), worth_a_quarter=True),
        Occasion("Christmas Day", date(year, 12, 25), worth_a_quarter=True),
    ]
    return sorted(found, key=lambda occasion: occasion.when)


def sundays(first: date, last: date) -> List[date]:
    """Every Sunday between two dates, both ends included."""
    if last < first:
        raise CalendarError("the last day comes before the first")
    ahead = (SUNDAY - first.weekday()) % 7
    found: List[date] = []
    when = first + timedelta(days=ahead)
    while when <= last:
        found.append(when)
        when += timedelta(days=7)
    return found


def practice_nights(first: date, last: date, weekday: int = TUESDAY) -> List[date]:
    """Every practice night in a range.

    Tuesday by default because more towers practise on a Tuesday than on
    anything else, and a default that is right most of the time saves most
    callers passing it.
    """
    if weekday not in DAY_NAMES:
        raise CalendarError(f"there is no day {weekday}")
    if last < first:
        raise CalendarError("the last day comes before the first")
    ahead = (weekday - first.weekday()) % 7
    found: List[date] = []
    when = first + timedelta(days=ahead)
    while when <= last:
        found.append(when)
        when += timedelta(days=7)
    return found


def clashes(nights: List[date], year: int) -> List[Occasion]:
    """Occasions that fall on a practice night.

    Worth knowing in advance: a practice on Ash Wednesday is a practice
    nobody comes to.
    """
    when = set(nights)
    return [occasion for occasion in occasions(year) if occasion.when in when]
