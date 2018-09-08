import pytest

from blueline.core.towers import (
    KILOGRAMS_PER_POUND,
    POUNDS_PER_HUNDREDWEIGHT,
    POUNDS_PER_QUARTER,
    Tower,
    TowerError,
    Weight,
    parse_weight,
    weight_from_pounds,
)
from blueline.errors import BluelineError, StageError


class TestWeight:
    def test_it_reads_as_a_peal_board_writes_it(self):
        assert str(Weight(23, 1, 14)) == "23-1-14"

    def test_it_totals_to_pounds(self):
        assert Weight(1, 0, 0).total_pounds == POUNDS_PER_HUNDREDWEIGHT
        assert Weight(0, 1, 0).total_pounds == POUNDS_PER_QUARTER
        assert Weight(0, 0, 7).total_pounds == 7

    def test_a_full_weight_totals_correctly(self):
        assert Weight(23, 1, 14).total_pounds == 23 * 112 + 28 + 14

    def test_it_converts_to_kilograms(self):
        assert Weight(1, 0, 0).kilograms == pytest.approx(112 * KILOGRAMS_PER_POUND)

    def test_nothing_can_weigh_less_than_nothing(self):
        with pytest.raises(TowerError):
            Weight(-1)

    def test_four_quarters_is_a_hundredweight_not_four_quarters(self):
        with pytest.raises(TowerError, match="more than a hundredweight"):
            Weight(23, 4, 0)

    def test_twenty_eight_pounds_is_a_quarter(self):
        with pytest.raises(TowerError, match="more than a quarter"):
            Weight(23, 0, 28)

    def test_weights_compare_by_what_they_weigh(self):
        assert Weight(8, 0, 0) < Weight(23, 0, 0)
        assert Weight(23, 0, 0) < Weight(23, 1, 0)
        assert Weight(23, 1, 0) < Weight(23, 1, 1)

    def test_a_tower_error_is_a_blueline_error(self):
        assert issubclass(TowerError, BluelineError)


class TestFromPounds:
    def test_it_breaks_a_total_up(self):
        assert weight_from_pounds(23 * 112 + 28 + 14) == Weight(23, 1, 14)

    def test_a_round_hundredweight_has_no_remainder(self):
        assert weight_from_pounds(112) == Weight(1, 0, 0)

    def test_nothing_weighs_nothing(self):
        assert weight_from_pounds(0) == Weight(0, 0, 0)

    def test_it_refuses_a_negative_total(self):
        with pytest.raises(TowerError):
            weight_from_pounds(-1)

    def test_it_goes_round_trip(self):
        for pounds in (0, 1, 27, 28, 111, 112, 2618):
            assert weight_from_pounds(pounds).total_pounds == pounds


class TestParseWeight:
    def test_it_reads_a_full_weight(self):
        assert parse_weight("23-1-14") == Weight(23, 1, 14)

    def test_it_reads_hundredweight_on_its_own(self):
        assert parse_weight("8") == Weight(8, 0, 0)

    def test_it_reads_two_parts(self):
        assert parse_weight("8-2") == Weight(8, 2, 0)

    def test_it_does_not_mind_stray_space(self):
        assert parse_weight("  23 - 1 - 14 ") == Weight(23, 1, 14)

    def test_something_that_is_not_numbers_is_refused(self):
        with pytest.raises(TowerError, match="not a weight"):
            parse_weight("heavy")

    def test_too_many_parts_are_refused(self):
        with pytest.raises(TowerError):
            parse_weight("23-1-14-9")

    def test_a_nonsense_weight_is_still_refused(self):
        with pytest.raises(TowerError):
            parse_weight("23-9-0")

    def test_it_goes_round_trip(self):
        for text in ("23-1-14", "8-0-0", "0-0-1"):
            assert str(parse_weight(text)) == text


class TestTower:
    def a_tower(self, **over) -> Tower:
        fields = {"place": "St Andrew, Marchgate", "bells": 8, "tenor": Weight(23, 1, 14)}
        fields.update(over)
        return Tower(**fields)

    def test_it_has_to_be_somewhere(self):
        with pytest.raises(TowerError, match="somewhere"):
            self.a_tower(place="   ")

    def test_it_has_to_have_a_sensible_number_of_bells(self):
        with pytest.raises(StageError):
            self.a_tower(bells=2)

    def test_a_ring_of_eight_rings_major(self):
        assert self.a_tower().rings(8)

    def test_a_ring_of_eight_rings_triples_and_minor(self):
        assert self.a_tower().rings(7)
        assert self.a_tower().rings(6)

    def test_a_ring_of_eight_does_not_ring_royal(self):
        assert not self.a_tower().rings(10)

    def test_nothing_below_singles_can_be_rung(self):
        assert not self.a_tower().rings(2)

    def test_a_heavy_tenor_is_remarked_on(self):
        assert self.a_tower().is_heavy

    def test_a_light_one_is_not(self):
        assert not self.a_tower(tenor=Weight(8, 0, 0)).is_heavy

    def test_it_reads_as_a_line(self):
        assert str(self.a_tower()) == "St Andrew, Marchgate, 8 bells, tenor 23-1-14"
