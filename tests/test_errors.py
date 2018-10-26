import pytest

from blueline.errors import (
    BluelineError,
    CallError,
    CoursingError,
    LibraryError,
    MethodError,
    NotationError,
    RowError,
    StageError,
    TitleError,
    TouchError,
)

EVERY_ERROR = [
    CallError,
    CoursingError,
    LibraryError,
    MethodError,
    NotationError,
    RowError,
    StageError,
    TitleError,
    TouchError,
]


class TestHierarchy:
    @pytest.mark.parametrize("error", EVERY_ERROR, ids=lambda e: e.__name__)
    def test_everything_hangs_off_the_one_base(self, error):
        assert issubclass(error, BluelineError)

    @pytest.mark.parametrize("error", EVERY_ERROR, ids=lambda e: e.__name__)
    def test_everything_is_still_a_value_error(self, error):
        # Callers that were catching ValueError before the tidy up keep working.
        assert issubclass(error, ValueError)

    def test_the_base_is_a_value_error_too(self):
        assert issubclass(BluelineError, ValueError)

    @pytest.mark.parametrize("error", EVERY_ERROR, ids=lambda e: e.__name__)
    def test_each_one_says_what_it_is_for(self, error):
        assert error.__doc__


class TestCatchingTheLot:
    def test_a_bad_stage_is_caught_by_the_base(self):
        from blueline.core.stage import check_stage

        with pytest.raises(BluelineError):
            check_stage(99)

    def test_a_bad_row_is_caught_by_the_base(self):
        from blueline.core.row import Row

        with pytest.raises(BluelineError):
            Row.parse("1123")

    def test_bad_notation_is_caught_by_the_base(self):
        from blueline.core.notation import parse_notation

        with pytest.raises(BluelineError):
            parse_notation("x1x1", 5)

    def test_a_bad_title_is_caught_by_the_base(self):
        from blueline.core.title import parse_title

        with pytest.raises(BluelineError):
            parse_title("Cambridge")

    def test_a_missing_method_is_caught_by_the_base(self):
        from blueline.db.repositories import MethodRepository
        from blueline.db.session import MEMORY_URL, create_all, make_engine, session_factory

        engine = make_engine(MEMORY_URL)
        create_all(engine)
        with session_factory(engine)() as session, pytest.raises(BluelineError):
            MethodRepository(session).get("Nowhere Surprise Major")

    def test_the_particular_type_still_comes_through(self):
        from blueline.core.stage import check_stage

        with pytest.raises(StageError):
            check_stage(99)


class TestModulesDoNotDefineTheirOwn:
    def test_the_modules_share_the_one_definition(self):
        from blueline import errors
        from blueline.core import method, row, stage

        assert row.RowError is errors.RowError
        assert stage.StageError is errors.StageError
        assert method.MethodError is errors.MethodError
