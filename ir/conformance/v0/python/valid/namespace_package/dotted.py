import pkg.common
from sdk import node


@node(version=1)
def dotted(*, mode: pkg.common.Mode = "a") -> None:
    """Pick a mode."""
