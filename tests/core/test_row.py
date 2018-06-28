import pytest

from blueline.core.row import Row, RowError
from blueline.core.stage import StageError


class TestParsing:
    def test_reads_a_row_written_out(self):
        assert Row.parse("13527486").bells == (1, 3, 5, 2, 7, 4, 8, 6)

    def test_reads_the_higher_bells(self):
        assert Row.parse("1234567890ET").stage == 12

    def test_does_not_mind_stray_space(self):
        assert Row.parse("  1324  ") == Row.parse("1324")

    def test_refuses_an_empty_row(self):
        with pytest.raises(RowError):
            Row.parse("")

    def test_refuses_a_row_with_a_bell_missing(self):
        with pytest.raises(RowError):
            Row.parse("1123")

    def test_refuses_a_row_with_a_bell_that_is_not_there(self):
        with pytest.raises(RowError):
            Row.parse("1239")

    def test_refuses_a_character_that_is_not_a_bell(self):
        with pytest.raises(StageError):
            Row.parse("12Z4")

    def test_writes_itself_back_out(self):
        assert str(Row.parse("13527486")) == "13527486"

    def test_repr_shows_the_row(self):
        assert repr(Row.parse("1324")) == "Row('1324')"


class TestRounds:
    def test_rounds_on_eight(self):
        assert str(Row.rounds(8)) == "12345678"

    def test_knows_it_is_rounds(self):
        assert Row.rounds(6).is_rounds

    def test_knows_when_it_is_not(self):
        assert not Row.parse("214365").is_rounds


class TestPlaces:
    def test_finds_the_bell_in_a_place(self):
        assert Row.parse("13527486")[2] == 3

    def test_places_count_from_one(self):
        assert Row.parse("13527486")[1] == 1

    def test_refuses_a_place_that_is_not_there(self):
        row = Row.parse("1234")
        with pytest.raises(RowError):
            row[0]
        with pytest.raises(RowError):
            row[5]

    def test_finds_where_a_bell_is_ringing(self):
        assert Row.parse("13527486").place_of(5) == 3

    def test_refuses_a_bell_that_is_not_there(self):
        with pytest.raises(RowError):
            Row.parse("1234").place_of(7)

    def test_length_is_the_stage(self):
        assert len(Row.parse("135264")) == 6


class TestTransposition:
    def test_rounds_leaves_a_row_alone(self):
        row = Row.parse("13527486")
        assert row.transposed_by(Row.rounds(8)) == row

    def test_transposing_rounds_gives_the_other_row_back(self):
        other = Row.parse("13527486")
        assert Row.rounds(8).transposed_by(other) == other

    def test_a_row_by_its_inverse_gives_rounds(self):
        row = Row.parse("13527486")
        assert row.transposed_by(row.inverse).is_rounds

    def test_transposition_is_not_commutative(self):
        first = Row.parse("13524")
        second = Row.parse("14235")
        assert first.transposed_by(second) != second.transposed_by(first)

    def test_refuses_two_different_stages(self):
        with pytest.raises(RowError):
            Row.parse("1234").transposed_by(Row.parse("123456"))

    def test_known_plain_bob_lead_head(self):
        # Plain Bob Minor comes round after five leads, each moving the bells
        # on by the same lead head.
        head = Row.parse("135264")
        row = Row.rounds(6)
        for _ in range(5):
            row = row.transposed_by(head)
        assert row.is_rounds


class TestInverse:
    def test_the_inverse_of_rounds_is_rounds(self):
        assert Row.rounds(8).inverse.is_rounds

    def test_inverting_twice_gives_the_row_back(self):
        row = Row.parse("13527486")
        assert row.inverse.inverse == row

    def test_a_known_inverse(self):
        assert str(Row.parse("13524").inverse) == "14253"


class TestParity:
    def test_rounds_is_even(self):
        assert Row.rounds(8).is_even

    def test_one_swap_makes_it_odd(self):
        assert not Row.rounds(8).swap(1).is_even

    def test_two_swaps_make_it_even_again(self):
        assert Row.rounds(8).swap(1).swap(3).is_even

    def test_parity_is_nought_or_one(self):
        assert Row.parse("13527486").parity in (0, 1)

    def test_half_of_all_rows_on_four_are_odd(self):
        from itertools import permutations

        rows = [Row(bells) for bells in permutations(range(1, 5))]
        odd = [row for row in rows if not row.is_even]
        assert len(odd) == len(rows) // 2


class TestSwap:
    def test_swaps_a_pair(self):
        assert str(Row.rounds(6).swap(3)) == "124356"

    def test_refuses_a_swap_off_the_top(self):
        with pytest.raises(RowError):
            Row.rounds(6).swap(6)

    def test_refuses_a_swap_below_the_first_place(self):
        with pytest.raises(RowError):
            Row.rounds(6).swap(0)


class TestCycles:
    def test_rounds_is_all_singletons(self):
        assert Row.rounds(5).cycles() == [(1,), (2,), (3,), (4,), (5,)]

    def test_a_plain_bob_lead_head_has_one_long_cycle(self):
        cycles = Row.parse("135264").cycles()
        lengths = sorted(len(cycle) for cycle in cycles)
        assert lengths == [1, 5]

    def test_every_bell_appears_once(self):
        cycles = Row.parse("13527486").cycles()
        assert sorted(bell for cycle in cycles for bell in cycle) == list(range(1, 9))

    def test_order_of_rounds_is_one(self):
        assert Row.rounds(8).order == 1

    def test_order_of_a_plain_bob_lead_head(self):
        assert Row.parse("135264").order == 5

    def test_applying_a_row_its_order_times_gives_rounds(self):
        head = Row.parse("13527486")
        row = Row.rounds(8)
        for _ in range(head.order):
            row = row.transposed_by(head)
        assert row.is_rounds


class TestHashing:
    def test_equal_rows_hash_alike(self):
        assert hash(Row.parse("1324")) == hash(Row.parse("1324"))

    def test_rows_go_in_a_set(self):
        assert len({Row.parse("1324"), Row.parse("1324"), Row.rounds(4)}) == 2
