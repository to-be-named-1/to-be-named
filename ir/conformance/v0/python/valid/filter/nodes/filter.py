"""Filter rows, written as the Python node SDK states it."""

from typing import Annotated, Literal

import ibis
from sdk import Column, node

type Operator = Literal["eq", "ne", "lt", "le", "gt", "ge"]


@node(plan="ibis", version=1, title="Filter rows", tags=["filter"])
def filter(
    data: ibis.Table,
    *,
    column: Annotated[str, Column(of="data")],
    operator: Operator = "ge",
    threshold: float = 0,
) -> ibis.Table:
    """Keep the rows whose column compares to the threshold.

    Args:
        data: The rows to filter.
        column: The column to compare.
        operator: How the column compares to the threshold.
        threshold: The value the column is compared to.
    """
    value = data[column]
    comparisons = {
        "eq": value == threshold,
        "ne": value != threshold,
        "lt": value < threshold,
        "le": value <= threshold,
        "gt": value > threshold,
        "ge": value >= threshold,
    }
    return data.filter(comparisons[operator])
