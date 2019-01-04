"""Proving a composition written the way it is published."""

from __future__ import annotations

from blueline.service.calls import prove_printed
from blueline.service.results import Reason

MAJOR = "Plain Bob Major"


class TestProving:
    def test_a_printed_calling_is_rung_through(self, loaded) -> None:
        view = prove_printed(loaded, MAJOR, "W H").unwrap()
        assert view.touch.length > 0

    def test_it_says_what_it_read(self, loaded) -> None:
        assert prove_printed(loaded, MAJOR, "W H H").unwrap().tidied == "W 2H"

    def test_the_original_is_kept(self, loaded) -> None:
        assert prove_printed(loaded, MAJOR, "  W H H ").unwrap().printed == "W H H"

    def test_it_expands_a_count(self, loaded) -> None:
        assert prove_printed(loaded, MAJOR, "3H").unwrap().positions == (
            "Home",
            "Home",
            "Home",
        )

    def test_parts_multiply_the_calls(self, loaded) -> None:
        one = prove_printed(loaded, MAJOR, "W H").unwrap()
        three = prove_printed(loaded, MAJOR, "W H x3").unwrap()
        assert three.calls == 3 * one.calls

    def test_the_calling_comes_back(self, loaded) -> None:
        view = prove_printed(loaded, MAJOR, "W H").unwrap()
        assert set(view.calling) <= {"p", "-"}

    def test_a_summary_reads_as_a_composition(self, loaded) -> None:
        assert prove_printed(loaded, MAJOR, "W H").unwrap().summary().startswith("W H:")

    def test_positions_spelled_out(self, loaded) -> None:
        assert prove_printed(loaded, MAJOR, "Wrong Home").ok


class TestRefusing:
    def test_a_method_nobody_has_stored(self, loaded) -> None:
        result = prove_printed(loaded, "Weasel Surprise Major", "W H")
        assert result.failure.reason is Reason.NOT_FOUND

    def test_something_that_is_not_a_position(self, loaded) -> None:
        result = prove_printed(loaded, MAJOR, "W ?? H")
        assert result.failure.reason is Reason.INVALID

    def test_nothing_to_read(self, loaded) -> None:
        assert prove_printed(loaded, MAJOR, "   ").failure.reason is Reason.INVALID

    def test_a_position_the_method_does_not_have(self, loaded) -> None:
        result = prove_printed(loaded, "Plain Bob Minor", "Fifths")
        assert result.failure.reason is Reason.INVALID

    def test_the_message_lists_what_there_is(self, loaded) -> None:
        result = prove_printed(loaded, "Plain Bob Minor", "Fifths")
        assert "try one of" in result.failure.detail
