from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta
from typing import Annotated, Literal

import polars as pl
from sdk import Minimum, node


@node(version=1)
def describe(
    data: pl.DataFrame,
    *,
    label: str = "all",
    limit: int = 10,
    ratio: float = 1,
    exact: bool = True,
    since: datetime,
    window: timedelta = timedelta(days=7, hours=12),
    first: date = date(2026, 1, 1),
    last: date,
    mode: Literal["fast", "full"] = "fast",
    level: Literal[1, 2, 3] = 2,
    sizes: Sequence[Annotated[int, Minimum(0)]] = [1, 2],
    weights: Mapping[str, float] = {},
    labels: Sequence[Mapping[str, str]] = [],
) -> pl.DataFrame:
    """Describe the rows in a window.

    Args:
        data: The rows.
        label: A label for the description,
            continued on a second line.
    """
    return data
