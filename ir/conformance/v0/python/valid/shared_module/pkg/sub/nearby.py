import ibis
from sdk import node

from .. import common
from ..common import Compared


@node(plan="ibis", version=1)
def nearby(data: ibis.Table, *, operator: common.Operator) -> Compared:
    return Compared(data, data.count())
