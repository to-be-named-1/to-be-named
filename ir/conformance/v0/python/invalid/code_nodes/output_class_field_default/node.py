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
    count: Value[int] = 0


@node()
def defaulted(data: pd.DataFrame) -> Result:
    return Result(data)
