"""The contract of a node, as read from its code, and of a node type, which a node-type document states."""

from dataclasses import Field, dataclass, field, fields
from typing import Any, Literal

IR_VERSION = 0
"""The IR version in which documents are written."""

type Json = Any
"""A value of the IR's data model: a string, number, boolean, null, list or mapping of these."""

DOCUMENT_FIELDS = ("ir_version", "kind", "image", "entry_point")
"""The fields of a node-type document that belong to the document rather than to the node it describes."""

type Table = Literal["ibis", "polars_lazy", "arrow", "polars_frame", "pandas"]
"""The table class node code works with: an Ibis table, a Polars lazy or data frame, an Arrow table or a pandas
data frame."""


@dataclass(frozen=True)
class Input:
    """An input port.

    Attributes:
        table: The table class the code receives, into which the runtime converts the port's data.
        type: The port's format type.
        optional: Whether the node runs without an edge to the port.
        many: Whether the port accepts several edges.
    """

    table: Table
    type: str = "tabular"
    optional: bool = False
    many: bool = False


@dataclass(frozen=True)
class Output:
    """An output port.

    Attributes:
        table: The table class the code returns, which the runtime converts from.
        type: The port's format type.
    """

    table: Table
    type: str = "tabular"


@dataclass(frozen=True, kw_only=True)
class CodeNodeContract:
    """What a node's code states about it, and the module and function that implement it.

    It is everything a node states; a node type states more (NodeTypeContract). Parameter and value schemas are
    mappings in the parameter profile of the IR specification.
    """

    module: str
    function: str
    language: Literal["python", "sql", "command"]
    plan: Literal["ibis", "polars"] | None
    title: str | None = None
    description: str | None = None
    tags: tuple[str, ...] = ()
    gpu: str | None = None
    memory_class: str | None = None
    memory_floor: str | None = None
    dialects: tuple[str, ...] = ()
    modes: tuple[str, ...] = ("batch",)
    inputs: dict[str, Input] = field(default_factory=dict[str, Input])
    outputs: dict[str, Output] = field(default_factory=dict[str, Output])
    params: dict[str, dict[str, Json]] = field(default_factory=dict[str, dict[str, Json]])
    values: dict[str, dict[str, Json]] = field(default_factory=dict[str, dict[str, Json]])
    grouping: str | None = None
    order: str | None = None
    seed: str | None = None
    side_effect_target: str | None = None

    @property
    def name(self) -> str:
        """The node's name, which is its function's name."""
        return self.function

    def mapping(self) -> dict[str, Json]:
        """Return the contract in the IR's data model, as the fields of a node-type document that describe a node."""
        return _in_document_order(self._fields())

    def _fields(self) -> dict[str, Json]:
        schema = "derived" if self.plan else "dynamic"
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "tags": list(self.tags),
            "language": self.language,
            "plan": self.plan,
            "modes": list(self.modes),
            "dialects": list(self.dialects),
            "inputs": {name: _input(port) for name, port in self.inputs.items()},
            "outputs": {name: {"type": port.type, "schema": schema} for name, port in self.outputs.items()},
            "params": {name: _parameter(schema) for name, schema in self.params.items()},
            "values": {name: _parameter(schema) for name, schema in self.values.items()},
            "grouping": {"parameter": self.grouping} if self.grouping else None,
            "order": {"parameter": self.order} if self.order else None,
            "seed": self.seed,
            "side_effects": {"target": self.side_effect_target} if self.side_effect_target else None,
            "gpu": self.gpu,
            "memory_floor": self.memory_floor,
            "memory_class": self.memory_class,
        }


@dataclass(frozen=True, kw_only=True)
class NodeTypeContract(CodeNodeContract):
    """The contract of a published node type: everything a node states, and what only a node type states."""

    version: int

    @classmethod
    def own_fields(cls) -> tuple[Field[Any], ...]:
        """Return the fields that only a node type states, which a code node's contract does not hold."""
        shared = {f.name for f in fields(CodeNodeContract)}
        return tuple(f for f in fields(cls) if f.name not in shared)

    def document(self, *, image: str) -> dict[str, Json]:
        """Return the node-type document this contract states, in the IR's data model.

        Args:
            image: The image that holds the implementation: the platform's base image or an image digest.
        """
        own = {f.name: getattr(self, f.name) for f in self.own_fields()}
        document = {
            "ir_version": IR_VERSION,
            "kind": "node_type",
            "image": image,
            "entry_point": f"{self.module}:{self.function}",
        }
        return _in_document_order(self._fields() | own | document)


# The keys of a node-type document and of a parameter schema, in the order in which node_type.schema.json and
# common.schema.json list them; the contract tests check both orders against the schema.
_DOCUMENT_ORDER = (
    "ir_version",
    "kind",
    "name",
    "version",
    "title",
    "description",
    "tags",
    "language",
    "plan",
    "image",
    "entry_point",
    "dialects",
    "modes",
    "inputs",
    "outputs",
    "params",
    "values",
    "grouping",
    "order",
    "seed",
    "side_effects",
    "gpu",
    "memory_floor",
    "memory_class",
)
_PARAMETER_ORDER = (
    "type",
    "format",
    "of",
    "items",
    "additionalProperties",
    "enum",
    "minimum",
    "maximum",
    "pattern",
    "default",
    "title",
    "description",
)


def _in_document_order(values: dict[str, Json]) -> dict[str, Json]:
    # Fields that hold nothing are left out; the types guarantee that a required field always holds a value.
    return _ordered({key: value for key, value in values.items() if not _empty(value)}, _DOCUMENT_ORDER)


def _parameter(schema: dict[str, Json]) -> dict[str, Json]:
    nested = {key: _parameter(schema[key]) for key in ("items", "additionalProperties") if key in schema}
    return _ordered(schema | nested, _PARAMETER_ORDER)


def _ordered(values: dict[str, Json], order: tuple[str, ...]) -> dict[str, Json]:
    # Keys the order does not list follow the others rather than being dropped, so that validation reports them.
    return {key: values[key] for key in order if key in values} | values


def _input(port: Input) -> dict[str, Json]:
    flags = {"optional": port.optional, "many": port.many}
    return {"type": port.type, **{flag: True for flag, set_ in flags.items() if set_}}


def _empty(value: Json) -> bool:
    return value is None or value == [] or value == {}
