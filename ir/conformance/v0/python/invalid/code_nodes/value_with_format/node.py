from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal

import ibis
import pandas as pd
import polars as pl
from sdk import Binding, Column, Minimum, Seed, Value, node


@dataclass(frozen=True)
class Result:
    data: pd.DataFrame
    key: Value[Annotated[str, Binding()]]


@node()
def formatted(data: pd.DataFrame) -> Result:
    return Result(data, "")
