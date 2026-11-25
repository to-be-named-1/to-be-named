from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Annotated

import ibis
from sdk import ColumnSelector, Maximum, Minimum, Value, node


@dataclass(frozen=True)
class Deduplicated:
    """The rows kept, the rows removed and how many were removed."""

    data: ibis.Table
    removed: ibis.Table
    removed_rows: Value[int]
    removed_share: Value[Annotated[float, Minimum(0), Maximum(1)]]
    duplicated_keys: Value[Sequence[str]]
    rows_by_key: Value[Mapping[str, int]]


@node(plan="ibis", version=1, tags=["distinct", "quality"], dialects=["snowflake"])
def deduplicate(data: ibis.Table, *, keys: Annotated[Sequence[str], ColumnSelector(of="data")]) -> Deduplicated:
    """Keep one row for each combination of keys."""
    kept = data.distinct(on=list(keys))
    by_key = data.group_by(keys[0]).agg(rows=data[keys[0]].count())
    return Deduplicated(
        data=kept,
        removed=data,
        removed_rows=data.count() - kept.count(),
        removed_share=1 - kept.count() / data.count(),
        duplicated_keys=by_key.filter(by_key.rows > 1)[keys[0]].collect(),
        rows_by_key=ibis.map(by_key[keys[0]].collect(), by_key.rows.collect()),
    )
