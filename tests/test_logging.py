import json
import logging

import pytest

from blueline.logging import DEV, JSON, bind, clear, configure, get_logger, unbind


@pytest.fixture(autouse=True)
def _tidy():
    clear()
    yield
    clear()
    configure()


class TestConfigure:
    def test_it_can_be_called_twice(self):
        configure()
        configure()

    def test_it_takes_the_json_shape(self, capsys):
        configure(JSON)
        get_logger("test").info("rang", method="Cambridge")
        line = capsys.readouterr().err.strip()
        assert json.loads(line)["method"] == "Cambridge"

    def test_the_json_shape_carries_the_event(self, capsys):
        configure(JSON)
        get_logger("test").info("rang")
        assert json.loads(capsys.readouterr().err.strip())["event"] == "rang"

    def test_it_stamps_the_time(self, capsys):
        configure(JSON)
        get_logger("test").info("rang")
        assert "timestamp" in json.loads(capsys.readouterr().err.strip())

    def test_it_records_the_level(self, capsys):
        configure(JSON)
        get_logger("test").warning("careful")
        assert json.loads(capsys.readouterr().err.strip())["level"] == "warning"

    def test_it_records_where_the_line_came_from(self, capsys):
        configure(JSON)
        get_logger("blueline.test").info("rang")
        assert json.loads(capsys.readouterr().err.strip())["logger"] == "blueline.test"

    def test_the_dev_shape_is_not_json(self, capsys):
        configure(DEV)
        get_logger("test").info("rang", method="Cambridge")
        line = capsys.readouterr().err.strip()
        assert "Cambridge" in line
        with pytest.raises(json.JSONDecodeError):
            json.loads(line)

    def test_a_level_can_be_set(self, capsys):
        configure(JSON, level=logging.WARNING)
        get_logger("test").info("quiet")
        assert capsys.readouterr().err.strip() == ""

    def test_a_line_above_the_level_gets_through(self, capsys):
        configure(JSON, level=logging.WARNING)
        get_logger("test").error("loud")
        assert "loud" in capsys.readouterr().err


class TestContext:
    def test_bound_fields_appear_on_every_line(self, capsys):
        configure(JSON)
        bind(request_id="abc")
        get_logger("test").info("one")
        get_logger("test").info("two")
        lines = [json.loads(line) for line in capsys.readouterr().err.strip().split("\n")]
        assert all(line["request_id"] == "abc" for line in lines)

    def test_unbinding_takes_them_off_again(self, capsys):
        configure(JSON)
        bind(request_id="abc")
        unbind("request_id")
        get_logger("test").info("after")
        assert "request_id" not in json.loads(capsys.readouterr().err.strip())

    def test_clearing_takes_everything_off(self, capsys):
        configure(JSON)
        bind(request_id="abc", method="Cambridge")
        clear()
        get_logger("test").info("after")
        line = json.loads(capsys.readouterr().err.strip())
        assert "request_id" not in line
        assert "method" not in line

    def test_a_field_on_one_line_does_not_leak_to_the_next(self, capsys):
        configure(JSON)
        log = get_logger("test")
        log.info("one", method="Cambridge")
        log.info("two")
        first, second = (json.loads(line) for line in capsys.readouterr().err.strip().split("\n"))
        assert first["method"] == "Cambridge"
        assert "method" not in second


class TestLogger:
    def test_it_binds_its_own_name(self, capsys):
        configure(JSON)
        get_logger("blueline.test").info("rang")
        assert json.loads(capsys.readouterr().err.strip())["logger"] == "blueline.test"

    def test_two_loggers_keep_their_own_names(self, capsys):
        configure(JSON)
        get_logger("one").info("a")
        get_logger("two").info("b")
        first, second = (json.loads(x) for x in capsys.readouterr().err.strip().split("\n"))
        assert first["logger"] == "one"
        assert second["logger"] == "two"
