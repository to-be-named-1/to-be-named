"""The names node code is written with: the node decorator, the markers and Value.

They do nothing when the code runs. Readers find their meaning in the source text, without executing it.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import ibis
    import polars

type Plan = Literal["ibis", "polars"]
type Gpu = Literal["none", "supported", "required"]
type MemoryClass = Literal["streaming", "blocking_spilling", "blocking_non_spilling"]

# ibis.Value rather than ibis.Scalar: Ibis declares operations on scalars, such as subtracting two counts, as
# returning types like NumericValue that cover columns too. Derivation checks that a plan's value is a scalar.
type Value[T] = T | ibis.Value | polars.Expr
"""A value output of an output class: the value itself in eager code, or an expression over the plan in a plan."""


def node[F: Callable[..., object]](
    *,
    plan: Plan | None = None,
    version: int | None = None,
    title: str | None = None,
    tags: Sequence[str] | None = None,
    gpu: Gpu | None = None,
    memory_class: MemoryClass | None = None,
    memory_floor: str | None = None,
    dialects: Sequence[str] | None = None,
) -> Callable[[F], F]:
    """Mark a module-level function as a node.

    Every argument must be a literal. The function is returned unchanged.

    Args:
        plan: "ibis" or "polars" for a function that returns a plan; None for eager code.
        version: The node type's version, required for a published node type.
        title: The node type's title.
        tags: Identifiers under which the palette groups and finds the node type.
        gpu: Whether the node can or must use a GPU.
        memory_class: A hint of the node's memory class.
        memory_floor: Memory the node needs regardless of its data, such as "1Gi".
        dialects: The warehouse dialects an Ibis plan supports.
    """

    def mark(function: F) -> F:
        return function

    return mark


@dataclass(frozen=True)
class Minimum:
    """The smallest value an integer or number parameter accepts."""

    value: int | float


@dataclass(frozen=True)
class Maximum:
    """The largest value an integer or number parameter accepts."""

    value: int | float


@dataclass(frozen=True)
class Pattern:
    """A regular expression that a string parameter's value must match."""

    regex: str


@dataclass(frozen=True)
class Title:
    """The title of a parameter."""

    text: str


@dataclass(frozen=True, kw_only=True)
class Column:
    """A string parameter naming one column of the input named by `of`."""

    of: str


@dataclass(frozen=True, kw_only=True)
class ColumnSelector:
    """A sequence parameter selecting columns of the input named by `of`; the code receives the names selected."""

    of: str


@dataclass(frozen=True)
class Binding:
    """A string parameter holding a logical name, bound to a resource per environment."""


@dataclass(frozen=True)
class Secret:
    """A string parameter holding a secret reference."""


@dataclass(frozen=True)
class Grouping:
    """Marks the column or column-selector parameter that supplies the node's grouping key."""


@dataclass(frozen=True)
class Order:
    """Marks the column or column-selector parameter that supplies the sort key the result depends on."""


@dataclass(frozen=True)
class Seed:
    """Marks the integer parameter that seeds the node's randomness."""


@dataclass(frozen=True)
class SideEffectTarget:
    """Marks the binding parameter naming the external target of the node's side effect."""
