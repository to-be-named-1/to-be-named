from pkg.common import Mode
from sdk import node


@node(version=1)
def from_module(*, mode: Mode = "a") -> None:
    """Pick a mode."""
