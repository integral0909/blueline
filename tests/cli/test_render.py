"""The pieces every table is built out of."""

from __future__ import annotations

from blueline.cli import render


class TestFields:
    """The shape five tables were separately building."""

    def test_it_takes_a_title(self) -> None:
        assert render.fields("Cambridge", []).title == "Cambridge"

    def test_a_none_value_is_left_out(self) -> None:
        table = render.fields("x", [("a", "1"), ("b", None), ("c", "3")])
        assert table.row_count == 2

    def test_values_that_are_there_are_kept(self) -> None:
        table = render.fields("x", [("a", "1"), ("b", "2")])
        assert table.row_count == 2

    def test_it_has_no_header(self) -> None:
        assert render.fields("x", []).show_header is False


class TestYesNo:
    def test_true(self) -> None:
        assert render.yes_no(True) == "yes"

    def test_false(self) -> None:
        assert render.yes_no(False) == "no"

    def test_false_can_say_more(self) -> None:
        assert render.yes_no(False, "no, 2 rows repeat") == "no, 2 rows repeat"


class TestPackage:
    """Everything the commands reach for is still reachable as render.thing."""

    def test_the_tables_are_all_exported(self) -> None:
        for name in ("method_table", "touch_table", "tower_table", "striking_table"):
            assert hasattr(render, name)

    def test_nothing_is_exported_twice(self) -> None:
        assert len(render.__all__) == len(set(render.__all__))
