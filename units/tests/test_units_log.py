import io
import json
import logging
import warnings
from collections.abc import Iterator

import pytest

from units import log


@pytest.fixture(autouse=True)
def restore_root_logger() -> Iterator[None]:
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)
    logging.captureWarnings(False)


def lines(stream: io.StringIO) -> list[str]:
    return stream.getvalue().splitlines()


def test_json_line_has_the_shared_keys_first() -> None:
    out = io.StringIO()
    log.configure(attrs={"attempt_id": "a1"}, stream=out)
    logging.getLogger("units.run").info("node %s done", "filter", extra={"rows": 3})

    (line,) = lines(out)
    assert line.startswith('{"time":"')
    assert ',"level":"INFO","msg":"node filter done",' in line
    record = json.loads(line)
    assert list(record)[:3] == ["time", "level", "msg"]
    del record["time"]
    assert record == {"level": "INFO", "msg": "node filter done", "attempt_id": "a1", "logger": "units.run", "rows": 3}


@pytest.mark.parametrize(
    ("levelno", "name"),
    [
        (logging.DEBUG, "DEBUG"),
        (logging.INFO, "INFO"),
        (logging.WARNING, "WARN"),
        (logging.ERROR, "ERROR"),
        (logging.CRITICAL, "ERROR+4"),
        (25, "INFO+2"),
        (5, "DEBUG-2"),
    ],
)
def test_level_names_match_go(levelno: int, name: str) -> None:
    assert log.level_name(levelno) == name


def test_level_filters() -> None:
    out = io.StringIO()
    log.configure(level="warn", stream=out)
    logging.getLogger("x").info("dropped")
    logging.getLogger("x").warning("kept")
    assert [json.loads(line)["msg"] for line in lines(out)] == ["kept"]


def test_exception_is_an_attribute() -> None:
    out = io.StringIO()
    log.configure(stream=out)
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        logging.getLogger("x").exception("failed")
    record = json.loads(out.getvalue())
    assert record["level"] == "ERROR"
    assert "RuntimeError: boom" in record["error"]


def test_text_format_quotes_like_go() -> None:
    out = io.StringIO()
    log.configure(format="text", stream=out)
    logging.getLogger("x").info("hello world", extra={"path": "a b", "plain": "v"})
    (line,) = lines(out)
    assert ' level=INFO msg="hello world" logger=x path="a b" plain=v' in line
    assert line.startswith("time=")


def test_warnings_are_logged() -> None:
    out = io.StringIO()
    log.configure(stream=out)
    warnings.warn("old API", DeprecationWarning, stacklevel=1)
    record = json.loads(out.getvalue())
    assert record["level"] == "WARN"
    assert "old API" in record["msg"]


def test_invalid_settings() -> None:
    with pytest.raises(ValueError, match="level"):
        log.configure(level="loud")
    with pytest.raises(ValueError, match="format"):
        log.configure(format="xml")  # type: ignore[arg-type]
