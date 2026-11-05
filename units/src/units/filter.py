"""Filter rows of a tabular input with an Ibis plan."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import ibis


def build(data: ibis.Table, column: str, operator: str = "ge", threshold: float = 0.0) -> ibis.Table:
    """Return a plan that keeps rows matching the predicate.

    The builder receives only an empty table and parameter values,
    never real data, so it must only build an Ibis expression.
    """
    # data[column] is typed as generic Column, which lacks ordering
    # operators in the stubs; the real type depends on the input schema.
    col: Any = data[column]
    if operator == "eq":
        predicate = col == threshold
    elif operator == "ne":
        predicate = col != threshold
    elif operator == "lt":
        predicate = col < threshold
    elif operator == "le":
        predicate = col <= threshold
    elif operator == "gt":
        predicate = col > threshold
    else:
        predicate = col >= threshold
    return data.filter(predicate)
