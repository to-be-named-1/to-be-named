import pandas as pd
from sdk import node


@node(title="Roll up")
def rollup(data: pd.DataFrame) -> pd.DataFrame:
    return data
