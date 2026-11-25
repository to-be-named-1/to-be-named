from pkg import common
from sdk import node


@node(version=1)
def from_package(*, mode: common.Mode = "a") -> None:
    """Pick a mode."""
