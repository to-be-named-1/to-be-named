from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal

import ibis
import pandas as pd
import polars as pl
from sdk import Binding, Column, Minimum, Seed, Value, node


@node()
def dated(data: pd.DataFrame, *, since: datetime = datetime(2026, 1, 1)) -> None: ...
