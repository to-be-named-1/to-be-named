from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal

import ibis
import pandas as pd
import polars as pl
from sdk import Binding, Column, Minimum, Seed, Value, node


@node()
def seeds(
    data: pd.DataFrame, *, first: Annotated[int, Seed()] = 0, second: Annotated[int, Seed()] = 1
) -> None: ...
