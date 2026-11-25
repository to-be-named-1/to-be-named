import pandas as pd
from common import Unit
from sdk import node


@node(version=1)
def rollup(data: pd.DataFrame, *, unit: Unit = "day") -> pd.DataFrame:
    return data
