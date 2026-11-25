from dataclasses import dataclass
from typing import Literal

import ibis
from sdk import Value

type Operator = Literal["lt", "gt"]
type Strict = Operator


@dataclass(frozen=True)
class Compared:
    data: ibis.Table
    matched: Value[int]
