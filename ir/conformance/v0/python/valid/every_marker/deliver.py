from collections.abc import Sequence
from typing import Annotated

import pyarrow as pa
from sdk import (
    Binding,
    Column,
    ColumnSelector,
    Grouping,
    Maximum,
    Minimum,
    Order,
    Pattern,
    Secret,
    Seed,
    SideEffectTarget,
    Title,
    node,
)


@node(version=2, gpu="none", memory_class="streaming", memory_floor="512Mi")
def deliver(
    data: pa.Table,
    *,
    key: Annotated[str, Column(of="data"), Order()],
    groups: Annotated[Sequence[str], ColumnSelector(of="data"), Grouping()] = [],
    target: Annotated[str, Binding(), SideEffectTarget(), Title("Target system")],
    token: Annotated[str, Secret()],
    batch: Annotated[int, Minimum(1), Maximum(10000)] = 500,
    prefix: Annotated[str, Pattern("^[a-z]+$")] = "run",
    seed: Annotated[int, Seed()] = 0,
) -> None:
    """Send rows to an external system in batches."""
