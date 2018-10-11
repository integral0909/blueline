"""Reading the council's method library."""

from __future__ import annotations

from typing import Optional

import pytest

from blueline.io.cccbr import CccbrError, read

HEADER = '<?xml version="1.0" encoding="utf-8"?>'
NS = "http://mathslib.co.uk/xml/method-library"


def library(*methods: str) -> str:
    inner = "".join(methods)
    return f'{HEADER}<collection xmlns="{NS}"><methodSet>{inner}</methodSet></collection>'


def entry(title: str, stage: str, notation: Optional[str]) -> str:
    parts = [f"<title>{title}</title>", f"<stage>{stage}</stage>"]
    if notation is not None:
        parts.append(f"<notation>{notation}</notation>")
    return "<method>" + "".join(parts) + "</method>"


CAMBRIDGE = entry("Cambridge Surprise Major", "8", "x38x14x1258x36x14x58x16x78,12")
PLAIN = entry("Plain Bob Minor", "6", "x16x16x16,12")


class TestReading:
    def test_reads_a_method(self) -> None:
        loaded = read(library(CAMBRIDGE))
        assert len(loaded) == 1
        assert loaded.methods[0].name == "Cambridge"
        assert loaded.methods[0].stage == 8

    def test_reads_several(self) -> None:
        loaded = read(library(CAMBRIDGE, PLAIN))
        assert [method.name for method in loaded.methods] == ["Cambridge", "Plain"]

    def test_notation_is_parsed_not_stored(self) -> None:
        loaded = read(library(CAMBRIDGE))
        assert loaded.methods[0].lead_length == 32

    def test_classification_is_worked_out(self) -> None:
        from blueline.core.classify import classify

        loaded = read(library(CAMBRIDGE))
        assert str(classify(loaded.methods[0])) == "Surprise"

    def test_a_clean_file_has_no_problems(self) -> None:
        loaded = read(library(CAMBRIDGE, PLAIN))
        assert loaded.ok
        assert loaded.summary() == "2 methods"

    def test_namespace_is_not_required(self) -> None:
        text = f"{HEADER}<collection>{CAMBRIDGE}</collection>"
        assert len(read(text)) == 1


class TestProblems:
    def test_one_bad_method_does_not_lose_the_rest(self) -> None:
        broken = entry("Broken Surprise Major", "5", "x1x1")
        loaded = read(library(CAMBRIDGE, broken, PLAIN))
        assert len(loaded) == 2
        assert len(loaded.problems) == 1

    def test_a_problem_names_the_method(self) -> None:
        broken = entry("Broken Surprise Major", "5", "x1x1")
        loaded = read(library(broken))
        assert "Broken Surprise Major" in loaded.problems[0]

    def test_missing_notation_is_a_problem(self) -> None:
        loaded = read(library(entry("Nameless Major", "8", None)))
        assert not loaded.ok
        assert "notation" in loaded.problems[0]

    def test_a_stage_that_is_not_a_number(self) -> None:
        loaded = read(library(entry("Odd Major", "eight", "x1x1")))
        assert "not a number" in loaded.problems[0]

    def test_summary_counts_problems(self) -> None:
        broken = entry("Broken Surprise Major", "5", "x1x1")
        loaded = read(library(CAMBRIDGE, broken))
        assert loaded.summary() == "1 methods, 1 could not be read"

    def test_not_xml_at_all(self) -> None:
        with pytest.raises(CccbrError, match="not xml"):
            read("this is a text file")

    def test_a_file_with_no_methods(self) -> None:
        with pytest.raises(CccbrError, match="no methods"):
            read(f"{HEADER}<collection></collection>")


class TestThroughDocuments:
    """A council file reaches the reader through the ordinary front door."""

    def test_read_dispatches_on_the_angle_bracket(self) -> None:
        from blueline.io.documents import read as read_document

        loaded = read_document(library(CAMBRIDGE, PLAIN))
        assert loaded.named() == ["Cambridge", "Plain"]

    def test_leading_blank_lines_do_not_confuse_it(self) -> None:
        from blueline.io.documents import read as read_document

        assert len(read_document("\n\n  " + library(CAMBRIDGE))) == 1

    def test_a_council_error_is_a_load_error(self) -> None:
        from blueline.io.loading import LoadError

        with pytest.raises(LoadError):
            read("not xml at all")
