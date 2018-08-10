import json

import pytest

from blueline.io.documents import (
    COMMENT,
    FORMAT,
    VERSION,
    DocumentError,
    LoadResult,
    read,
    read_json,
    read_lines,
    to_record,
    write_json,
    write_lines,
)
from blueline.library import standard_methods
from tests.methods import CAMBRIDGE_MAJOR, PLAIN_BOB_MINOR

SOME = [PLAIN_BOB_MINOR, CAMBRIDGE_MAJOR]


class TestRecord:
    def test_it_keeps_the_three_things_that_matter(self):
        assert to_record(PLAIN_BOB_MINOR) == {
            "name": "Plain",
            "stage": 6,
            "notation": "x16x16x16x16x16x12",
        }

    def test_it_does_not_store_anything_derived(self):
        # A file claiming a method is Surprise when the notation says otherwise
        # would have to be either believed or argued with.
        assert "classification" not in to_record(CAMBRIDGE_MAJOR)


class TestJson:
    def test_it_writes_a_header(self):
        document = json.loads(write_json(SOME))
        assert document["format"] == FORMAT
        assert document["version"] == VERSION

    def test_it_writes_every_method(self):
        assert len(json.loads(write_json(SOME))["methods"]) == 2

    def test_a_collection_goes_round_trip(self):
        result = read_json(write_json(SOME))
        assert result.ok
        assert [m.notation for m in result.methods] == [m.notation for m in SOME]

    def test_the_whole_standard_set_goes_round_trip(self):
        methods = standard_methods()
        result = read_json(write_json(methods))
        assert len(result) == len(methods)
        assert [m.name for m in result.methods] == [m.name for m in methods]

    def test_something_that_is_not_json_is_refused(self):
        with pytest.raises(DocumentError, match="not json"):
            read_json("{{{")

    def test_a_list_at_the_top_is_refused(self):
        with pytest.raises(DocumentError, match="object"):
            read_json("[]")

    def test_a_document_of_another_format_is_refused(self):
        with pytest.raises(DocumentError, match="not a"):
            read_json(json.dumps({"format": "something.else", "methods": []}))

    def test_a_document_with_no_methods_list_is_refused(self):
        with pytest.raises(DocumentError, match="list of methods"):
            read_json(json.dumps({"format": FORMAT, "version": 1}))

    def test_an_empty_collection_reads_as_nothing(self):
        result = read_json(json.dumps({"format": FORMAT, "version": 1, "methods": []}))
        assert result.ok
        assert len(result) == 0

    def test_one_bad_record_does_not_lose_the_others(self):
        document = json.loads(write_json(SOME))
        document["methods"].insert(1, {"name": "x", "stage": 5, "notation": "x1x1"})
        result = read_json(json.dumps(document))
        assert len(result) == 2
        assert len(result.problems) == 1

    def test_it_says_which_record_was_wrong(self):
        document = json.loads(write_json(SOME))
        document["methods"].append({"name": "x", "stage": 5, "notation": "x1x1"})
        assert "method 3" in read_json(json.dumps(document)).problems[0]

    def test_a_record_missing_a_field_is_reported(self):
        document = {"format": FORMAT, "methods": [{"name": "x", "stage": 6}]}
        assert "notation" in read_json(json.dumps(document)).problems[0]

    def test_a_record_that_is_not_an_object_is_reported(self):
        document = {"format": FORMAT, "methods": ["nonsense"]}
        assert "not a method" in read_json(json.dumps(document)).problems[0]


class TestLines:
    def test_it_writes_a_comment_header(self):
        assert write_lines(SOME).startswith(COMMENT)

    def test_it_writes_one_method_per_line(self):
        body = [line for line in write_lines(SOME).splitlines() if not line.startswith(COMMENT)]
        assert len(body) == 2

    def test_a_collection_goes_round_trip(self):
        result = read_lines(write_lines(SOME))
        assert result.ok
        assert [m.notation for m in result.methods] == [m.notation for m in SOME]

    def test_the_whole_standard_set_goes_round_trip(self):
        methods = standard_methods()
        assert len(read_lines(write_lines(methods))) == len(methods)

    def test_comments_and_blanks_are_ignored(self):
        text = f"{COMMENT} a note\n\n   \nPlain, 6, x16x16x16,12\n"
        result = read_lines(text)
        assert len(result) == 1

    def test_stray_space_around_the_fields_is_ignored(self):
        assert len(read_lines("  Plain ,  6 , x16x16x16,12  ")) == 1

    def test_a_line_with_the_wrong_number_of_fields_is_reported(self):
        result = read_lines("Plain, 6")
        assert not result.ok
        assert "line 1" in result.problems[0]

    def test_a_line_with_bad_notation_is_reported(self):
        result = read_lines("Nonsense, 5, x1x1")
        assert not result.ok
        assert "line 1" in result.problems[0]

    def test_a_line_with_a_stage_that_is_not_a_number_is_reported(self):
        assert not read_lines("Plain, six, x16").ok

    def test_one_bad_line_does_not_lose_the_others(self):
        text = "Plain, 6, x16x16x16,12\nrubbish\nCambridge, 6, x36x14x12x36x14x56,12"
        result = read_lines(text)
        assert len(result) == 2
        assert len(result.problems) == 1

    def test_the_line_number_is_the_real_one(self):
        text = f"{COMMENT} header\n\nPlain, 6, x16x16x16,12\nrubbish\n"
        assert "line 4" in read_lines(text).problems[0]


class TestReadEither:
    def test_it_spots_json(self):
        assert read(write_json(SOME)).ok

    def test_it_spots_lines(self):
        assert read(write_lines(SOME)).ok

    def test_leading_space_does_not_confuse_it(self):
        assert read("\n\n  " + write_json(SOME)).ok


class TestResult:
    def test_an_empty_result_is_ok(self):
        assert LoadResult().ok

    def test_it_counts_what_it_read(self):
        assert len(read_lines("Plain, 6, x16x16x16,12")) == 1

    def test_a_clean_read_summarises_as_a_count(self):
        assert read_lines("Plain, 6, x16x16x16,12").summary() == "1 methods"

    def test_a_dirty_read_says_how_many_failed(self):
        assert "could not be read" in read_lines("rubbish").summary()
