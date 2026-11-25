import helpers
import pandas as pd
from sdk import node


@helpers.cache
@node()
def cached(data: pd.DataFrame) -> None: ...
