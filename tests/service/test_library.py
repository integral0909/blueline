from blueline.service import library as service
from blueline.service.results import Reason


class TestDescribe:
    def test_it_analyses_notation_without_storing_it(self, repository):
        result = service.describe("Cambridge", 8, "x38x14x1258x36x14x58x16x78,12")
        assert result.ok
        assert str(result.unwrap().title) == "Cambridge Surprise Major"
        assert repository.count() == 0

    def test_bad_notation_comes_back_as_invalid(self):
        result = service.describe("Nonsense", 5, "x1x1")
        assert not result.ok
        assert result.failure.reason is Reason.INVALID

    def test_a_stage_out_of_range_comes_back_as_invalid(self):
        assert service.describe("Nonsense", 99, "x18").failure.reason is Reason.INVALID

    def test_it_says_what_was_wrong(self):
        assert "even stage" in service.describe("x", 5, "x1x1").failure.detail


class TestStore:
    def test_a_method_can_be_stored(self, repository):
        result = service.store(repository, "Cambridge", 6, "x36x14x12x36x14x56,12")
        assert result.ok
        assert repository.count() == 1

    def test_the_same_method_twice_is_refused(self, repository):
        service.store(repository, "Cambridge", 6, "x36x14x12x36x14x56,12")
        again = service.store(repository, "Cambridge", 6, "x36x14x12x36x14x56,12")
        assert again.failure.reason is Reason.ALREADY_EXISTS

    def test_bad_notation_is_refused_before_it_gets_near_the_database(self, repository):
        assert service.store(repository, "x", 5, "x1x1").failure.reason is Reason.INVALID
        assert repository.count() == 0


class TestFetch:
    def test_it_finds_a_stored_method(self, loaded):
        result = service.fetch(loaded, "Cambridge Surprise Major")
        assert result.ok
        assert result.unwrap().course_length == 224

    def test_lookup_ignores_case(self, loaded):
        assert service.fetch(loaded, "cambridge surprise major").ok

    def test_something_missing_comes_back_as_not_found(self, loaded):
        result = service.fetch(loaded, "Nowhere Surprise Major")
        assert result.failure.reason is Reason.NOT_FOUND
        assert "Nowhere" in result.failure.detail


class TestRemove:
    def test_it_removes_a_stored_method(self, loaded):
        before = loaded.count()
        assert service.remove(loaded, "Plain Bob Minor").ok
        assert loaded.count() == before - 1

    def test_removing_something_missing_is_not_found(self, loaded):
        assert service.remove(loaded, "Nowhere Surprise Major").failure.reason is Reason.NOT_FOUND


class TestSearch:
    def test_it_finds_by_name(self, loaded):
        found = service.search(loaded, name="cambridge").unwrap()
        assert [str(report.title) for report in found] == [
            "Cambridge Surprise Minor",
            "Cambridge Surprise Major",
        ]

    def test_it_finds_the_surprise_major(self, loaded):
        found = service.search(loaded, classification="Surprise", stage=8).unwrap()
        assert len(found) == 5

    def test_a_search_matching_nothing_succeeds_with_nothing(self, loaded):
        result = service.search(loaded, name="nowhere")
        assert result.ok
        assert result.unwrap() == []


class TestImport:
    def test_it_reads_a_json_collection(self, repository):
        from blueline.io.documents import write_json
        from blueline.library import standard_methods

        report = service.import_methods(repository, write_json(standard_methods())).unwrap()
        assert len(report.added) == 15
        assert repository.count() == 15

    def test_it_reads_the_line_format_too(self, repository):
        text = "Plain, 6, x16x16x16,12\nCambridge, 6, x36x14x12x36x14x56,12"
        report = service.import_methods(repository, text).unwrap()
        assert len(report.added) == 2

    def test_anything_already_there_is_skipped(self, loaded):
        from blueline.io.documents import write_json
        from blueline.library import standard_methods

        report = service.import_methods(loaded, write_json(standard_methods())).unwrap()
        assert report.added == ()
        assert len(report.skipped) == 15

    def test_a_bad_record_is_reported_and_the_rest_go_in(self, repository):
        text = "Plain, 6, x16x16x16,12\nrubbish\nCambridge, 6, x36x14x12x36x14x56,12"
        report = service.import_methods(repository, text).unwrap()
        assert len(report.added) == 2
        assert len(report.problems) == 1

    def test_a_file_it_cannot_read_at_all_is_invalid(self, repository):
        result = service.import_methods(repository, '{"format": "something.else"}')
        assert result.failure.reason is Reason.INVALID

    def test_the_summary_says_what_happened(self, repository):
        text = "Plain, 6, x16x16x16,12\nrubbish"
        report = service.import_methods(repository, text).unwrap()
        assert "1 added" in report.summary()
        assert "could not be read" in report.summary()

    def test_it_totals_what_it_looked_at(self, loaded):
        from blueline.io.documents import write_json
        from blueline.library import standard_methods

        assert service.import_methods(loaded, write_json(standard_methods())).unwrap().total == 15


class TestExport:
    def test_it_writes_json_by_default(self, loaded):
        text = service.export_methods(loaded).unwrap()
        assert text.lstrip().startswith("{")

    def test_it_can_write_lines(self, loaded):
        text = service.export_methods(loaded, shape="lines").unwrap()
        assert text.lstrip().startswith("#")

    def test_what_it_writes_reads_back(self, loaded, repository):
        from blueline.io.documents import read

        text = service.export_methods(loaded).unwrap()
        assert len(read(text)) == 15

    def test_it_can_export_one_stage(self, loaded):
        from blueline.io.documents import read

        text = service.export_methods(loaded, stage=6).unwrap()
        loaded_back = read(text)
        assert all(method.stage == 6 for method in loaded_back.methods)

    def test_an_empty_library_exports_an_empty_collection(self, repository):
        from blueline.io.documents import read

        assert len(read(service.export_methods(repository).unwrap())) == 0

    def test_a_format_it_does_not_know_is_invalid(self, loaded):
        assert service.export_methods(loaded, shape="xml").failure.reason is Reason.INVALID

    def test_what_is_exported_puts_back_what_is_removed(self, loaded):
        # loaded and repository are the same object, so a genuinely empty
        # library has to be made by taking something out of this one.
        text = service.export_methods(loaded).unwrap()
        service.remove(loaded, "Plain Bob Minor")
        assert loaded.find("Plain Bob Minor") is None

        report = service.import_methods(loaded, text).unwrap()
        assert report.added == ("Plain Bob Minor",)
        assert len(report.skipped) == 14
        assert loaded.find("Plain Bob Minor") is not None
