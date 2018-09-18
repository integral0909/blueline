from datetime import timedelta

import pytest

from blueline.core.ringing_up import (
    DEFAULT_RAISE_MINUTES,
    RAISE_MINUTES,
    Session,
    SessionError,
    speed_for,
    time_for,
)
from blueline.errors import BluelineError


class TestSession:
    def a_session(self, **over) -> Session:
        fields = {"bells": 8, "changes": 1250, "peal_speed": 30.0}
        fields.update(over)
        return Session(**fields)

    def test_it_times_the_ringing(self):
        assert self.a_session().ringing_time == timedelta(minutes=1250 / 30)

    def test_a_faster_band_takes_less_time(self):
        quick = self.a_session(peal_speed=35.0).ringing_time
        slow = self.a_session(peal_speed=25.0).ringing_time
        assert quick < slow

    def test_raising_takes_longer_on_more_bells(self):
        assert self.a_session(bells=12).raise_time > self.a_session(bells=6).raise_time

    def test_lowering_takes_as_long_as_raising(self):
        session = self.a_session()
        assert session.lower_time == session.raise_time

    def test_a_ring_with_no_rule_of_thumb_falls_back(self):
        assert self.a_session(bells=9).raise_time == timedelta(minutes=DEFAULT_RAISE_MINUTES)

    def test_not_raising_takes_no_time(self):
        assert self.a_session(raised=False).raise_time == timedelta()

    def test_not_lowering_takes_no_time(self):
        assert self.a_session(lowered=False).lower_time == timedelta()

    def test_bells_already_up_still_get_lowered(self):
        session = self.a_session(raised=False, lowered=True)
        assert session.raise_time == timedelta()
        assert session.lower_time == timedelta(minutes=RAISE_MINUTES[8])

    def test_the_total_is_the_three_added_up(self):
        session = self.a_session()
        assert session.total_time == session.raise_time + session.ringing_time + session.lower_time

    def test_the_overhead_is_the_time_not_ringing_changes(self):
        session = self.a_session()
        assert session.overhead == session.raise_time + session.lower_time

    def test_a_session_with_neither_has_no_overhead(self):
        assert self.a_session(raised=False, lowered=False).overhead == timedelta()

    def test_a_negative_length_is_refused(self):
        with pytest.raises(SessionError, match="negative"):
            self.a_session(changes=-1)

    def test_a_speed_of_nothing_is_refused(self):
        with pytest.raises(SessionError, match="some speed"):
            self.a_session(peal_speed=0)

    def test_a_session_error_is_a_blueline_error(self):
        assert issubclass(SessionError, BluelineError)


class TestSummary:
    def test_it_says_both_times(self):
        summary = Session(bells=8, changes=1250).summary()
        assert "1250 changes" in summary
        assert "on the bells" in summary

    def test_a_short_stretch_reads_in_minutes(self):
        assert "m" in Session(bells=8, changes=60).summary()

    def test_a_long_one_reads_in_hours(self):
        assert "h" in Session(bells=8, changes=5000).summary()


class TestSpeed:
    def test_it_works_out_rows_a_minute(self):
        assert speed_for(1250, timedelta(minutes=50)) == 25.0

    def test_a_performance_in_no_time_is_refused(self):
        with pytest.raises(SessionError, match="some time"):
            speed_for(1250, timedelta())

    def test_speed_and_time_are_the_two_sides_of_one_sum(self):
        span = time_for(1250, speed=25.0)
        assert speed_for(1250, span) == pytest.approx(25.0)


class TestTimeFor:
    def test_a_peal_at_thirty_takes_about_three_hours(self):
        span = time_for(5040, speed=30.0)
        assert 2.5 < span.total_seconds() / 3600 < 3.0

    def test_a_faster_speed_takes_less_time(self):
        assert time_for(5040, speed=35.0) < time_for(5040, speed=25.0)

    def test_a_speed_of_nothing_is_refused(self):
        with pytest.raises(SessionError):
            time_for(1250, speed=0)

    def test_nothing_takes_no_time(self):
        assert time_for(0) == timedelta()
