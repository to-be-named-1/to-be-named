import datetime as dt
import typing
from typing import TYPE_CHECKING

import sdk as s
from sdk import Column as Col

if TYPE_CHECKING:
    import polars as pl


@s.node(plan="polars", version=1)
def flag(
    rows: pl.LazyFrame,
    *,
    column: typing.Annotated[str, Col(of="rows")],
    horizon: dt.timedelta = dt.timedelta(minutes=90),
) -> pl.LazyFrame:
    return rows
