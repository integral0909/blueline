"""The converters, checked without an application around them."""

from __future__ import annotations

from typing import Dict, Set

from blueline.api import convert
from blueline.api.convert import common, methods, records, touches
from blueline.core.music import count_music
from blueline.core.peals import standing_of
from blueline.core.rounds import RoundsAt
from blueline.service.method_views import HandbellView, ImportReport
from tests.packages import duplicates, exported

MODULES = {"common": common, "methods": methods, "records": records, "touches": touches}


def defined_in(module) -> Set[str]:
    """The converters a module defines itself, not the ones it imports."""
    return {
        name
        for name in dir(module)
        if not name.startswith("_")
        and callable(getattr(module, name))
        and getattr(getattr(module, name), "__module__", None) == module.__name__
    }


class TestSplit:
    def test_every_module_has_converters_in_it(self):
        for label, module in MODULES.items():
            assert defined_in(module), f"{label} has none"

    def test_no_converter_is_defined_twice(self):
        seen: Dict[str, str] = {}
        for label, module in MODULES.items():
            for name in defined_in(module):
                assert name not in seen, f"{name} in both {seen.get(name)} and {label}"
                seen[name] = label

    def test_everything_is_reachable_from_the_package(self):
        for module in MODULES.values():
            for name in defined_in(module):
                assert hasattr(convert, name), name

    def test_common_holds_what_more_than_one_subject_needs(self):
        assert "counted_music" in defined_in(common)

    def test_nothing_is_exported_from_two_places(self):
        assert duplicates(convert) == set()

    def test_every_subject_reaches_the_package(self):
        assert {"method_out", "touch_out", "competition_out"} <= exported(convert)


class TestCommon:
    def test_it_flattens_a_music_count(self):
        out = convert.counted_music(count_music([]))
        assert out.named == {}
        assert out.runs_at_back == {}


class TestTouches:
    def test_a_standing_carries_both_fields(self):
        out = convert.standing_out(standing_of(5040, 7))
        assert out.counts_as == "peal"
        assert out.short_by == 0

    def test_rounds_that_never_happened_converts_to_nothing(self):
        assert convert.rounds_at_out(None) is None

    def test_rounds_that_did_carries_where(self):
        out = convert.rounds_at_out(RoundsAt(row=60, lead=5, at_lead_end=True))
        assert out.row == 60
        assert out.lead == 5
        assert out.at_lead_end


class TestMethods:
    def test_an_import_report_carries_every_list(self):
        out = convert.import_out(ImportReport(added=("a",), skipped=("b",), problems=("c",)))
        assert out.added == ["a"]
        assert out.skipped == ["b"]
        assert out.problems == ["c"]
        assert out.total == 2

    def test_a_handbell_pair_carries_its_bells(self):
        out = convert.handbell_pair_out(
            HandbellView(pair="1-2", bells=(1, 2), crossings=(3,), together=(0,))
        )
        assert out.bells == [1, 2]
        assert out.crossings == [3]


class TestRecords:
    def test_a_leaderboard_flattens_to_names_and_counts(self):
        out = convert.counts_out([("Ann", 3), ("Bob", 1)])
        assert [entry.name for entry in out] == ["Ann", "Bob"]
        assert out[0].count == 3

    def test_an_empty_leaderboard_converts_to_nothing(self):
        assert convert.counts_out([]) == []
