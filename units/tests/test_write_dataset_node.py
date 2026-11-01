"""Tests of the write_dataset node type."""

from pathlib import Path

import pyarrow as pa
import pyarrow.dataset as ds
from units.write_dataset import run

TABLE = pa.table({"id": [1, 2, 3], "name": ["a", "b", "c"]})


def read_back(target: Path) -> pa.Table:
    return ds.dataset(target, format="parquet").to_table()


def test_writes_every_row(tmp_path: Path) -> None:
    run(TABLE, str(tmp_path / "out"))

    assert read_back(tmp_path / "out").sort_by("id").equals(TABLE)


def test_returns_the_number_of_rows_written(tmp_path: Path) -> None:
    assert run(TABLE, str(tmp_path / "out")) == {"rows_written": 3}


def test_append_keeps_the_existing_rows(tmp_path: Path) -> None:
    run(TABLE, str(tmp_path / "out"))
    run(TABLE, str(tmp_path / "out"), mode="append")

    assert read_back(tmp_path / "out").num_rows == 6


def test_overwrite_replaces_the_existing_rows(tmp_path: Path) -> None:
    run(TABLE, str(tmp_path / "out"))
    run(TABLE, str(tmp_path / "out"), mode="overwrite")

    assert read_back(tmp_path / "out").num_rows == 3
