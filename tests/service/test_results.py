import pytest

from blueline.service.results import (
    Failure,
    Reason,
    already_exists,
    invalid,
    not_found,
    succeeded,
)


class TestResult:
    def test_a_success_is_ok(self):
        assert succeeded(3).ok

    def test_a_failure_is_not(self):
        assert not not_found("gone").ok

    def test_unwrapping_a_success_gives_the_value(self):
        assert succeeded("Cambridge").unwrap() == "Cambridge"

    def test_unwrapping_a_failure_complains(self):
        with pytest.raises(ValueError, match="unwrapped a failed result"):
            not_found("gone").unwrap()

    def test_a_success_carries_no_failure(self):
        assert succeeded(1).failure is None

    def test_a_failure_carries_no_value(self):
        assert invalid("no").value is None


class TestReasons:
    def test_not_found_says_so(self):
        assert not_found("gone").failure.reason is Reason.NOT_FOUND

    def test_already_exists_says_so(self):
        assert already_exists("there").failure.reason is Reason.ALREADY_EXISTS

    def test_invalid_says_so(self):
        assert invalid("nonsense").failure.reason is Reason.INVALID

    def test_the_detail_comes_through(self):
        assert not_found("no method called x").failure.detail == "no method called x"

    def test_a_failure_reads_as_its_detail(self):
        assert str(Failure(Reason.INVALID, "bad notation")) == "bad notation"

    def test_reasons_are_strings_so_they_serialise(self):
        assert Reason.NOT_FOUND == "not-found"

    def test_the_three_reasons_are_distinct(self):
        assert len({Reason.NOT_FOUND, Reason.ALREADY_EXISTS, Reason.INVALID}) == 3
