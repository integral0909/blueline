"""The standard set has to hang together.

Rutland got in with a wrong notation and stayed in, because on its own it
looked fine: true plain course, right lead length, right treble line. What
gave it away was sitting next to the others. These are the checks that compare
methods against each other rather than against themselves.
"""

from __future__ import annotations

from typing import List

from collections import defaultdict

import pytest

from blueline.analysis import analyse
from blueline.core.method import Method
from blueline.library import STANDARD, standard_methods


@pytest.fixture(scope="module")
def methods() -> List[Method]:
    return standard_methods()


def ident(method: Method) -> str:
    return f"{method.name} {method.stage}"


class TestEachOnItsOwn:
    def test_every_notation_parses(self, methods):
        assert len(methods) == len(STANDARD)

    @pytest.mark.parametrize("entry", STANDARD, ids=lambda e: f"{e[0]} {e[1]}")
    def test_each_rings_a_true_plain_course(self, entry):
        name, stage, notation = entry
        assert Method.from_notation(name, stage, notation).is_true_course()

    def test_no_two_entries_are_the_same_method(self, methods):
        titles = [str(analyse(method).title) for method in methods]
        assert len(set(titles)) == len(titles)

    def test_every_method_has_a_hunt_bell_or_is_a_principle(self, methods):
        for method in methods:
            report = analyse(method)
            assert method.hunt_bells or report.is_principle


class TestAgainstEachOther:
    def test_the_surprise_major_methods_share_a_lead_head(self, methods):
        heads = defaultdict(list)
        for method in methods:
            if method.stage == 8 and str(analyse(method).classification) == "Surprise":
                heads[str(method.lead_head)].append(method.name)

        # Bristol has an eighths place lead end and belongs on its own. The
        # seconds place ones all have to agree, and a singleton among them is
        # what a wrong notation looks like.
        seconds = {
            head: names
            for head, names in heads.items()
            if head != str(next(m.lead_head for m in methods if m.name == "Bristol"))
        }
        for head, names in seconds.items():
            assert len(names) > 1, f"{names[0]} sits alone on {head}"

    def test_the_seconds_place_group_is_the_one_expected(self, methods):
        together = sorted(
            method.name
            for method in methods
            if method.stage == 8 and str(method.lead_head) == "15738264"
        )
        assert together == ["Cambridge", "Lincolnshire", "Superlative", "Yorkshire"]

    def test_the_same_lead_end_change_does_not_promise_the_same_lead_head(self, methods):
        # Worth writing down, because assuming it did was the first version of
        # this test. Cambridge and London are both Surprise Minor with a
        # seconds place lead end and their lead heads differ, which is exactly
        # why the lead head groups have names of their own.
        minor = {
            method.name: str(method.lead_head)
            for method in methods
            if method.stage == 6 and str(analyse(method).classification) == "Surprise"
        }
        assert minor["Cambridge"] != minor["London"]

    def test_every_plain_method_has_a_lead_twice_its_stage(self, methods):
        for method in methods:
            if str(analyse(method).classification) in {"Bob", "Place"}:
                assert method.lead_length == method.stage * 2, ident(method)

    def test_every_surprise_method_has_a_lead_four_times_its_stage(self, methods):
        for method in methods:
            if str(analyse(method).classification) == "Surprise":
                assert method.lead_length == method.stage * 4, ident(method)


class TestCoverage:
    def test_it_spans_several_stages(self, methods):
        assert len({method.stage for method in methods}) >= 4

    def test_it_has_more_than_one_family(self, methods):
        families = {str(analyse(method).classification) for method in methods}
        assert len(families) >= 2

    def test_the_names_are_bare_names_not_titles(self, methods):
        for method in methods:
            assert " Bob" not in method.name
            assert " Surprise" not in method.name
