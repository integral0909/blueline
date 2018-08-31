import pytest

from blueline.core.bands import Band, BandError, band_of
from blueline.errors import BluelineError, StageError

EIGHT = ["Ann", "Bob", "Cara", "Dan", "Eve", "Finn", "Gus", "Hana"]


class TestBuilding:
    def test_a_band_covers_its_stage(self):
        assert Band(ringers=tuple(EIGHT)).stage == 8

    def test_it_refuses_a_stage_it_cannot_ring(self):
        with pytest.raises(StageError):
            Band(ringers=("Ann", "Bob"))

    def test_nobody_can_ring_two_bells(self):
        with pytest.raises(BandError, match="two bells"):
            Band(ringers=("Ann", "Ann", "Cara", "Dan"))

    def test_the_same_name_in_another_case_is_still_the_same_person(self):
        with pytest.raises(BandError):
            Band(ringers=("Ann", "ANN", "Cara", "Dan"))

    def test_every_bell_needs_somebody(self):
        with pytest.raises(BandError, match="every bell"):
            Band(ringers=("Ann", "   ", "Cara", "Dan"))

    def test_the_conductor_has_to_be_in_the_band(self):
        with pytest.raises(BandError, match="conductor"):
            Band(ringers=tuple(EIGHT), conductor=9)

    def test_the_conductor_defaults_to_the_treble(self):
        assert Band(ringers=tuple(EIGHT)).conductor == 1

    def test_a_band_error_is_a_blueline_error(self):
        assert issubclass(BandError, BluelineError)


class TestWhoRingsWhat:
    def test_it_says_who_is_on_a_bell(self):
        assert Band(ringers=tuple(EIGHT)).on(3) == "Cara"

    def test_it_trims_the_names(self):
        assert Band(ringers=("  Ann  ", "Bob", "Cara", "Dan")).on(1) == "Ann"

    def test_a_bell_that_is_not_there_is_refused(self):
        band = Band(ringers=tuple(EIGHT))
        with pytest.raises(BandError):
            band.on(9)
        with pytest.raises(BandError):
            band.on(0)

    def test_it_says_which_bell_somebody_is_on(self):
        assert Band(ringers=tuple(EIGHT)).bell_of("Cara") == 3

    def test_finding_somebody_ignores_case_and_space(self):
        assert Band(ringers=tuple(EIGHT)).bell_of("  cara ") == 3

    def test_somebody_who_is_not_there_is_refused(self):
        with pytest.raises(BandError, match="not in this band"):
            Band(ringers=tuple(EIGHT)).bell_of("Nobody")

    def test_it_names_the_conductor(self):
        band = Band(ringers=tuple(EIGHT), conductor=8)
        assert band.conducted_by == "Hana"


class TestRingingAStage:
    def test_a_band_of_eight_rings_major(self):
        assert Band(ringers=tuple(EIGHT)).rings(8)

    def test_a_band_of_eight_rings_triples_with_the_tenor_covering(self):
        assert Band(ringers=tuple(EIGHT)).rings(7)

    def test_a_band_of_eight_does_not_ring_minor(self):
        assert not Band(ringers=tuple(EIGHT)).rings(6)

    def test_a_band_of_eight_does_not_ring_royal(self):
        assert not Band(ringers=tuple(EIGHT)).rings(10)

    def test_a_band_of_six_rings_doubles(self):
        assert Band(ringers=tuple(EIGHT[:6])).rings(5)


class TestBandOf:
    def test_it_names_the_conductor_rather_than_counting(self):
        band = band_of(EIGHT, conductor="Hana")
        assert band.conductor == 8
        assert band.conducted_by == "Hana"

    def test_with_no_conductor_it_falls_back_to_the_treble(self):
        assert band_of(EIGHT).conductor == 1

    def test_a_conductor_who_is_not_in_the_band_is_refused(self):
        with pytest.raises(BandError):
            band_of(EIGHT, conductor="Nobody")


class TestPealBoard:
    def test_one_line_per_bell(self):
        assert len(band_of(EIGHT).lines()) == 8

    def test_each_line_names_the_bell_and_the_ringer(self):
        assert band_of(EIGHT).lines()[2] == "3 Cara"

    def test_the_conductor_is_marked(self):
        assert band_of(EIGHT, conductor="Hana").lines()[7] == "8 Hana (c)"

    def test_only_the_conductor_is_marked(self):
        marked = [line for line in band_of(EIGHT, conductor="Ann").lines() if "(c)" in line]
        assert len(marked) == 1

    def test_the_higher_bells_use_their_symbols(self):
        twelve = [*EIGHT, "Ivy", "Jed", "Kit", "Lex"]
        assert band_of(twelve).lines()[-1].startswith("T ")
