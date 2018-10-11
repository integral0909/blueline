"""The result both readers hand back."""

from __future__ import annotations

from blueline.errors import BluelineError
from blueline.io.loading import LoadError, LoadResult
from tests.methods import CAMBRIDGE_MINOR, PLAIN_BOB_MINOR


class TestLoadResult:
    def test_empty_is_ok(self) -> None:
        assert LoadResult().ok

    def test_a_problem_is_not_ok(self) -> None:
        assert not LoadResult(problems=["method 1: no notation"]).ok

    def test_length_counts_methods_not_problems(self) -> None:
        result = LoadResult(methods=[PLAIN_BOB_MINOR], problems=["a", "b"])
        assert len(result) == 1

    def test_summary_of_a_clean_read(self) -> None:
        result = LoadResult(methods=[PLAIN_BOB_MINOR, CAMBRIDGE_MINOR])
        assert result.summary() == "2 methods"

    def test_summary_mentions_problems(self) -> None:
        result = LoadResult(methods=[PLAIN_BOB_MINOR], problems=["line 4: bad stage"])
        assert result.summary() == "1 methods, 1 could not be read"

    def test_named_lists_what_was_read(self) -> None:
        result = LoadResult(methods=[PLAIN_BOB_MINOR, CAMBRIDGE_MINOR])
        assert result.named() == ["Plain", "Cambridge"]

    def test_named_of_nothing(self) -> None:
        assert LoadResult().named() == []


class TestLoadError:
    def test_is_a_blueline_error(self) -> None:
        assert issubclass(LoadError, BluelineError)

    def test_both_readers_raise_it(self) -> None:
        from blueline.io.cccbr import CccbrError
        from blueline.io.documents import DocumentError

        assert issubclass(CccbrError, LoadError)
        assert issubclass(DocumentError, LoadError)
