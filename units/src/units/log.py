"""Structured logging for units.

Units write one JSON object per line to standard error, or text, with the keys the platform's Go processes
write: ``time``, ``level`` and ``msg``, then the attributes. Levels read as Go's do: ``DEBUG``, ``INFO``,
``WARN``, ``ERROR``, and offsets such as ``ERROR+4`` for Python's ``CRITICAL``.

The unit runtime calls :func:`configure` once; node code and the libraries it uses log through the standard
:mod:`logging` module as usual.
"""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import Mapping
from datetime import datetime
from typing import IO, Any, Literal

Format = Literal["json", "text"]

LEVELS: Mapping[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "error": logging.ERROR,
}

# Attributes every LogRecord has; anything else on a record came from ``extra=`` and is logged as an attribute.
_RECORD_FIELDS = frozenset(vars(logging.LogRecord("", 0, "", 0, "", (), None))) | {"message", "asctime"}

_GO_LEVELS = ((8, "ERROR"), (4, "WARN"), (0, "INFO"), (-4, "DEBUG"))


def level_name(levelno: int) -> str:
    """Return the name Go's log/slog gives the level matching Python's ``levelno``."""
    go_level = round((levelno - logging.INFO) * 4 / 10)
    for base, name in _GO_LEVELS:
        if go_level >= base:
            return name if go_level == base else f"{name}{go_level - base:+d}"
    return f"DEBUG{go_level + 4:+d}"


def _attributes(record: logging.LogRecord, attrs: Mapping[str, Any]) -> dict[str, Any]:
    line: dict[str, Any] = dict(attrs)
    line["logger"] = record.name
    line.update((key, value) for key, value in vars(record).items() if key not in _RECORD_FIELDS)
    return line


class JsonFormatter(logging.Formatter):
    """Formats a record as one JSON object: ``time``, ``level``, ``msg``, then the attributes."""

    def __init__(self, attrs: Mapping[str, Any] | None = None) -> None:
        super().__init__()
        self._attrs = dict(attrs or {})

    def format(self, record: logging.LogRecord) -> str:
        line: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created).astimezone().isoformat(),
            "level": level_name(record.levelno),
            "msg": record.getMessage(),
        }
        line.update(_attributes(record, self._attrs))
        if record.exc_info:
            line["error"] = self.formatException(record.exc_info)
        if record.stack_info:
            line["stack"] = self.formatStack(record.stack_info)
        return json.dumps(line, default=str, ensure_ascii=False, separators=(",", ":"))


def _text_value(value: Any) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    if text == "" or any(c.isspace() or c in '"=' for c in text):
        return json.dumps(text, ensure_ascii=False)
    return text


class TextFormatter(logging.Formatter):
    """Formats a record as ``key=value`` pairs in the order and quoting of Go's text output."""

    def __init__(self, attrs: Mapping[str, Any] | None = None) -> None:
        super().__init__()
        self._attrs = dict(attrs or {})

    def format(self, record: logging.LogRecord) -> str:
        pairs: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created).astimezone().isoformat(timespec="milliseconds"),
            "level": level_name(record.levelno),
            "msg": record.getMessage(),
        }
        pairs.update(_attributes(record, self._attrs))
        if record.exc_info:
            pairs["error"] = self.formatException(record.exc_info)
        return " ".join(f"{key}={_text_value(value)}" for key, value in pairs.items())


def configure(
    level: str = "info",
    format: Format = "json",
    attrs: Mapping[str, Any] | None = None,
    stream: IO[str] | None = None,
) -> None:
    """Configure the root logger to write every record of ``level`` or above to ``stream``.

    ``level`` is debug, info, warn or error, and ``format`` json or text, as in the Go processes' log settings.
    ``attrs``, such as the attempt's identifiers, are added to every line. ``stream`` defaults to standard
    error. Warnings issued with :mod:`warnings` are logged as well, so that every line of output is structured.
    """
    if level.lower() not in LEVELS:
        raise ValueError(f"log level {level!r} is not one of {', '.join(LEVELS)}")
    if format not in ("json", "text"):
        raise ValueError(f"log format {format!r} is not json or text")
    handler = logging.StreamHandler(stream if stream is not None else sys.stderr)
    handler.setFormatter(JsonFormatter(attrs) if format == "json" else TextFormatter(attrs))
    root = logging.getLogger()
    for existing in root.handlers[:]:
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(LEVELS[level.lower()])
    logging.captureWarnings(True)
