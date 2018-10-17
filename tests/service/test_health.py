"""Whether the service can actually answer."""

from __future__ import annotations

from sqlalchemy import text

from blueline.service.health import (
    FAILING,
    OK,
    SLOW_STATUS,
    Check,
    Health,
    check_database,
    readiness,
)


class TestCheck:
    def test_a_passing_check(self) -> None:
        assert Check(name="database", status=OK).passed

    def test_a_slow_check_still_passes(self) -> None:
        assert Check(name="database", status=SLOW_STATUS).passed

    def test_a_failing_check_does_not(self) -> None:
        assert not Check(name="database", status=FAILING).passed


class TestHealth:
    def test_everything_passing_is_ready(self) -> None:
        report = Health(checks=(Check("database", OK),))
        assert report.ready
        assert report.status == OK

    def test_one_failure_is_not_ready(self) -> None:
        report = Health(checks=(Check("database", OK), Check("cache", FAILING)))
        assert not report.ready
        assert report.status == FAILING

    def test_slow_is_reported_but_still_ready(self) -> None:
        report = Health(checks=(Check("database", SLOW_STATUS),))
        assert report.ready
        assert report.status == SLOW_STATUS

    def test_failing_lists_what_went_wrong(self) -> None:
        report = Health(checks=(Check("database", FAILING, detail="gone"),))
        assert report.failing()[0].detail == "gone"

    def test_nothing_checked_is_ready(self) -> None:
        assert Health(checks=()).ready


class TestDatabaseCheck:
    def test_a_working_database_passes(self, session) -> None:
        assert check_database(session).status == OK

    def test_it_says_how_long_it_took(self, session) -> None:
        assert check_database(session).took >= 0

    def test_a_slow_threshold_of_nothing_reads_as_slow(self, session) -> None:
        assert check_database(session, slow=0.0).status == SLOW_STATUS

    def test_a_missing_table_fails(self, session) -> None:
        session.execute(text("drop table methods"))
        check = check_database(session)
        assert check.status == FAILING
        assert check.detail

    def test_the_detail_is_one_line(self, session) -> None:
        session.execute(text("drop table methods"))
        assert "\n" not in check_database(session).detail

    def test_readiness_checks_the_database(self, session) -> None:
        report = readiness(session)
        assert [check.name for check in report.checks] == ["database"]

    def test_readiness_of_a_broken_database(self, session) -> None:
        session.execute(text("drop table methods"))
        assert not readiness(session).ready
