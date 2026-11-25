from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated

import polars as pl
from sdk import Column, ColumnSelector, Grouping, Order, node


@dataclass(frozen=True)
class Balances:
    balances: pl.LazyFrame


@node(plan="polars", version=1, title="Running balance with a cap", tags=["running_total", "finance"])
def capped_balance(
    movements: pl.LazyFrame,
    *,
    amount: Annotated[str, Column(of="movements")],
    time: Annotated[str, Column(of="movements"), Order()],
    cap: float,
    group_by: Annotated[Sequence[str], ColumnSelector(of="movements"), Grouping()] = [],
) -> Balances:
    return Balances(movements)
