from pathlib import Path

import ibis
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from units.read_parquet import build


def test_plan_has_the_columns_of_the_file(tmp_path: Path) -> None:
    path = tmp_path / "data.parquet"
    pq.write_table(pa.table({"id": [1, 2, 3], "name": ["a", "b", "c"]}), path)

    plan = build(str(path))

    assert isinstance(plan, ibis.Table)
    assert plan.columns == ("id", "name")


def test_plan_returns_every_row(tmp_path: Path) -> None:
    path = tmp_path / "data.parquet"
    pq.write_table(pa.table({"id": [1, 2, 3]}), path)

    assert build(str(path)).to_pyarrow().column("id").to_pylist() == [1, 2, 3]


def test_plan_reads_every_file_matching_a_pattern(tmp_path: Path) -> None:
    pq.write_table(pa.table({"id": [1, 2]}), tmp_path / "part-0.parquet")
    pq.write_table(pa.table({"id": [3]}), tmp_path / "part-1.parquet")

    rows = build(str(tmp_path / "*.parquet")).to_pyarrow().column("id").to_pylist()

    assert sorted(rows) == [1, 2, 3]


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(Exception, match="missing"):
        build(str(tmp_path / "missing.parquet"))
