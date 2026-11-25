from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal

import ibis
import pandas as pd
import polars as pl
from sdk import Binding, Column, Minimum, Seed, Value, node


Mode = Literal["a", "b"]


@node()
def assigned(data: pd.DataFrame, *, mode: Mode = "a") -> None: ...
