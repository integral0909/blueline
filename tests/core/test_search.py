from blueline.core.calls import plain_bob_calls
from blueline.core.search import Found, Limits, search_callings, shortest_touch
from blueline.core.touch import parse_calling
from blueline.core.truth import prove_touch
from tests.methods import PLAIN_BOB_DOUBLES, PLAIN_BOB_MINOR

PB5 = plain_bob_calls(5)
PB6 = plain_bob_calls(6)


class TestLimits:
    def test_it_wants_something_inside_the_range(self):
        assert Limits(min_length=10, max_length=100).wants(50)

    def test_it_does_not_want_something_too_short(self):
        assert not Limits(min_length=10).wants(5)

    def test_it_does_not_want_something_too_long(self):
        assert not Limits(max_length=100).wants(200)

    def test_the_bounds_are_inclusive(self):
        limits = Limits(min_length=10, max_length=100)
        assert limits.wants(10)
        assert limits.wants(100)


class TestFound:
    def test_it_reads_as_the_calling_and_its_length(self):
        assert str(Found(calling="---", leads=3, length=36)) == "--- (36)"


class TestSearch:
    def test_it_finds_the_plain_course(self):
        found, _ = search_callings(PLAIN_BOB_MINOR, PB6, Limits(max_found=3))
        assert found[0].calling == "ppppp"
        assert found[0].length == 60

    def test_everything_it_finds_comes_round(self):
        found, _ = search_callings(PLAIN_BOB_DOUBLES, PB5, Limits(max_found=6))
        for entry in found:
            touch = parse_calling(PLAIN_BOB_DOUBLES, PB5, entry.calling)
            assert touch.comes_round()

    def test_everything_it_finds_is_true(self):
        found, _ = search_callings(PLAIN_BOB_DOUBLES, PB5, Limits(max_found=6))
        for entry in found:
            touch = parse_calling(PLAIN_BOB_DOUBLES, PB5, entry.calling)
            assert prove_touch(touch).is_true

    def test_the_lengths_it_reports_are_right(self):
        found, _ = search_callings(PLAIN_BOB_MINOR, PB6, Limits(max_found=4))
        for entry in found:
            assert entry.length == entry.leads * PLAIN_BOB_MINOR.lead_length

    def test_it_comes_back_shortest_first(self):
        found, _ = search_callings(PLAIN_BOB_DOUBLES, PB5, Limits(max_found=8))
        assert [entry.length for entry in found] == sorted(entry.length for entry in found)

    def test_it_respects_a_minimum_length(self):
        found, _ = search_callings(PLAIN_BOB_DOUBLES, PB5, Limits(min_length=100, max_found=4))
        assert all(entry.length >= 100 for entry in found)

    def test_it_respects_a_maximum_length(self):
        found, _ = search_callings(PLAIN_BOB_DOUBLES, PB5, Limits(max_length=60, max_found=8))
        assert all(entry.length <= 60 for entry in found)

    def test_it_stops_at_the_count_it_was_given(self):
        found, _ = search_callings(PLAIN_BOB_DOUBLES, PB5, Limits(max_found=2))
        assert len(found) == 2

    def test_stopping_early_is_reported(self):
        _, exhausted = search_callings(PLAIN_BOB_DOUBLES, PB5, Limits(max_found=2))
        assert not exhausted

    def test_a_search_that_finishes_says_so(self):
        _, exhausted = search_callings(
            PLAIN_BOB_MINOR, PB6, Limits(max_length=60, max_leads=5, max_found=50)
        )
        assert exhausted

    def test_the_node_cap_stops_it(self):
        found, exhausted = search_callings(
            PLAIN_BOB_MINOR, PB6, Limits(max_found=999, max_nodes=50)
        )
        assert not exhausted

    def test_the_calls_can_be_restricted(self):
        found, _ = search_callings(PLAIN_BOB_DOUBLES, PB5, Limits(max_found=4), allowed="p-")
        assert all("s" not in entry.calling for entry in found)

    def test_restricting_to_plains_finds_only_the_course(self):
        found, _ = search_callings(PLAIN_BOB_MINOR, PB6, Limits(max_found=5), allowed="p")
        assert [entry.calling for entry in found] == ["ppppp"]

    def test_a_symbol_it_does_not_know_is_ignored(self):
        found, _ = search_callings(PLAIN_BOB_MINOR, PB6, Limits(max_found=2), allowed="pz")
        assert found[0].calling == "ppppp"


class TestShortest:
    def test_it_finds_the_plain_course_when_nothing_is_asked(self):
        assert shortest_touch(PLAIN_BOB_MINOR, PB6).length == 60

    def test_it_finds_something_over_a_length(self):
        found = shortest_touch(PLAIN_BOB_DOUBLES, PB5, min_length=100)
        assert found is not None
        assert found.length >= 100

    def test_what_it_finds_is_true(self):
        found = shortest_touch(PLAIN_BOB_DOUBLES, PB5, min_length=100)
        touch = parse_calling(PLAIN_BOB_DOUBLES, PB5, found.calling)
        assert touch.comes_round()
        assert prove_touch(touch).is_true

    def test_nothing_long_enough_gives_nothing(self):
        assert shortest_touch(PLAIN_BOB_DOUBLES, PB5, min_length=100_000) is None
