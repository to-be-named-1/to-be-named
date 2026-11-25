import ibis
import pkg.common
from pkg.common import Operator
from sdk import node


@node(plan="ibis", version=1)
def compare(data: ibis.Table, *, operator: Operator = "lt", strict: pkg.common.Strict = "gt") -> pkg.common.Compared:
    return pkg.common.Compared(data, data.count())
