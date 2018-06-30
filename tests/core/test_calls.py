import pytest

from blueline.core.calls import (
    PLAIN,
    Call,
    CallError,
    apply_call,
    called_lead,
    grandsire_calls,
    plain_bob_calls,
)
from blueline.core.notation import format_notation, parse_change
from blueline.core.row import Row
from tests.methods import GRANDSIRE_DOUBLES, PLAIN_BOB_MAJOR, PLAIN_BOB_MINOR


class TestCall:
    def test_reads_as_its_symbol(self):
        assert str(plain_bob_calls(6)["-"]) == "-"

    def test_carries_the_stage_of_its_change(self):
        assert plain_bob_calls(8)["-"].stage == 8

    def test_a_lead_end_call_replaces_the_last_change(self):
        call = plain_bob_calls(6)["-"]
        assert call.index_in(12) == 11

    def test_an_offset_call_replaces_an_earlier_one(self):
        call = grandsire_calls(5)["-"]
        assert call.index_in(10) == 8

    def test_refuses_a_negative_offset(self):
        with pytest.raises(CallError):
            Call("Silly", "?", parse_change("14", 6), offset=-1)

    def test_refuses_a_call_that_does_not_fit_the_lead(self):
        call = Call("Deep", "?", parse_change("14", 6), offset=20)
        with pytest.raises(CallError):
            call.index_in(12)

    def test_a_plain_lead_has_a_symbol_of_its_own(self):
        assert PLAIN == "p"


class TestPlainBobCalls:
    def test_the_bob_makes_fourths(self):
        assert str(plain_bob_calls(6)["-"].change) == "14"

    def test_the_single_holds_thirds_as_well(self):
        assert str(plain_bob_calls(6)["s"].change) == "1234"

    def test_both_go_at_the_lead_end(self):
        for call in plain_bob_calls(8).values():
            assert call.offset == 0

    def test_there_is_no_room_at_singles(self):
        with pytest.raises(CallError):
            plain_bob_calls(3)


class TestGrandsireCalls:
    def test_the_bob_makes_thirds(self):
        assert str(grandsire_calls(5)["-"].change) == "3"

    def test_the_single_holds_the_back_bells(self):
        assert str(grandsire_calls(5)["s"].change) == "345"

    def test_both_come_a_change_before_the_lead_end(self):
        for call in grandsire_calls(5).values():
            assert call.offset == 1

    def test_grandsire_needs_five_bells(self):
        with pytest.raises(CallError):
            grandsire_calls(4)


class TestApplyCall:
    def test_a_plain_lead_is_the_method_untouched(self):
        assert apply_call(PLAIN_BOB_MINOR.changes, None) == list(PLAIN_BOB_MINOR.changes)

    def test_a_bob_swaps_the_lead_end_change(self):
        called = apply_call(PLAIN_BOB_MINOR.changes, plain_bob_calls(6)["-"])
        assert format_notation(called) == "x16x16x16x16x16x14"

    def test_the_rest_of_the_lead_is_left_alone(self):
        called = apply_call(PLAIN_BOB_MINOR.changes, plain_bob_calls(6)["-"])
        assert called[:-1] == list(PLAIN_BOB_MINOR.changes)[:-1]

    def test_a_call_does_not_change_the_length_of_the_lead(self):
        called = apply_call(PLAIN_BOB_MINOR.changes, plain_bob_calls(6)["s"])
        assert len(called) == PLAIN_BOB_MINOR.lead_length

    def test_refuses_a_call_from_another_stage(self):
        with pytest.raises(CallError):
            apply_call(PLAIN_BOB_MINOR.changes, plain_bob_calls(8)["-"])


class TestCalledLead:
    def test_a_plain_lead_ends_on_the_plain_lead_head(self):
        rows = called_lead(PLAIN_BOB_MINOR.changes, None, Row.rounds(6))
        assert rows[-1] == PLAIN_BOB_MINOR.lead_head

    def test_a_bob_sends_the_bells_somewhere_else(self):
        rows = called_lead(PLAIN_BOB_MINOR.changes, plain_bob_calls(6)["-"], Row.rounds(6))
        assert str(rows[-1]) == "123564"

    def test_a_single_is_different_again(self):
        rows = called_lead(PLAIN_BOB_MINOR.changes, plain_bob_calls(6)["s"], Row.rounds(6))
        assert str(rows[-1]) == "132564"

    def test_three_bobs_bring_plain_bob_minor_round(self):
        # The three bob touch every ringer learns early on.
        call = plain_bob_calls(6)["-"]
        row = Row.rounds(6)
        for _ in range(3):
            row = called_lead(PLAIN_BOB_MINOR.changes, call, row)[-1]
        assert row.is_rounds

    def test_two_bobs_do_not(self):
        call = plain_bob_calls(6)["-"]
        row = Row.rounds(6)
        for _ in range(2):
            row = called_lead(PLAIN_BOB_MINOR.changes, call, row)[-1]
        assert not row.is_rounds

    def test_six_singles_bring_it_round(self):
        call = plain_bob_calls(6)["s"]
        row = Row.rounds(6)
        for _ in range(6):
            row = called_lead(PLAIN_BOB_MINOR.changes, call, row)[-1]
        assert row.is_rounds

    def test_it_takes_five_bobs_at_major(self):
        # A fourths place bob holds the first three bells and sends the rest
        # round in a ring, so the number of bobbed leads is the stage less
        # three: three at minor, five at major.
        call = plain_bob_calls(8)["-"]
        row = Row.rounds(8)
        for _ in range(5):
            row = called_lead(PLAIN_BOB_MAJOR.changes, call, row)[-1]
        assert row.is_rounds

    def test_four_bobs_do_not_do_it_at_major(self):
        call = plain_bob_calls(8)["-"]
        row = Row.rounds(8)
        for _ in range(4):
            row = called_lead(PLAIN_BOB_MAJOR.changes, call, row)[-1]
        assert not row.is_rounds

    def test_a_grandsire_bob_changes_the_lead_head(self):
        rows = called_lead(GRANDSIRE_DOUBLES.changes, grandsire_calls(5)["-"], Row.rounds(5))
        assert rows[-1] != GRANDSIRE_DOUBLES.lead_head
        assert str(rows[-1]) == "14523"

    def test_a_called_lead_is_the_same_length_as_a_plain_one(self):
        plain = called_lead(PLAIN_BOB_MINOR.changes, None, Row.rounds(6))
        bobbed = called_lead(PLAIN_BOB_MINOR.changes, plain_bob_calls(6)["-"], Row.rounds(6))
        assert len(plain) == len(bobbed)
