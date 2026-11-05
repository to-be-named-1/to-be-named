"""The built-in node type read_parquet."""

import ibis


def build(path: str) -> ibis.Table:
    """Return the plan that reads the Parquet file or files at `path`."""
    return ibis.read_parquet(path)
