from collections.abc import Sequence

import pandas as pd
import polars as pl
import pyarrow as pa
from sdk import node


@node(version=1)
def combine(
    main: pd.DataFrame,
    parts: Sequence[pa.Table],
    extra: pl.DataFrame | None = None,
    more: Sequence[pa.Table] = [],
) -> pa.Table:
    """Combine several inputs into one table."""
    return pa.concat_tables(parts)
