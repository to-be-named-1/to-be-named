"""The built-in node type write_dataset."""

import uuid
from typing import Literal

import pyarrow as pa
import pyarrow.dataset as ds


def run(data: pa.Table, target: str, mode: Literal["append", "overwrite"] = "append") -> dict[str, int]:
    """Write `data` as Parquet files into the directory `target`, and return the number of rows written.

    `append` adds new files next to the existing ones. `overwrite` first removes the existing Parquet files.
    """
    behavior = "delete_matching" if mode == "overwrite" else "overwrite_or_ignore"
    ds.write_dataset(
        data,
        target,
        format="parquet",
        basename_template=f"part-{uuid.uuid4().hex}-{{i}}.parquet",
        existing_data_behavior=behavior,
    )
    return {"rows_written": data.num_rows}
