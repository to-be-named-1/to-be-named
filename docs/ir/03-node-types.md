# Node types

What a node type declares, how its parameters are typed and checked, what the platform derives instead of reading from a declaration, and how code nodes obtain their contract ([D57](../architecture/decisions/0057-node-type-contract.md)).

## Node-type documents

A node-type document, of kind `node_type`, describes one version of one node type: its contract and a reference to its implementation. The SDK generates node-type documents from a node type's code, for built-in node types and plugins alike. A node-type document MAY also be written by hand, and a reader holds it to the same rules. Built-in node types, plugins and code nodes are compiled, planned and run in the same way; none has a path of its own.

```yaml
ir_version: 0
kind: node_type
name: outliers
version: 1
title: Flag outliers
tags: [anomaly]
language: python
image: platform-base
entry_point: example_nodes.outliers:outliers
modes: [batch]
inputs:
  data: { type: tabular }
outputs:
  flagged: { type: tabular, schema: dynamic }
params:
  columns:   { type: array, format: column_selector, of: data }
  method:    { type: string, enum: [iqr, zscore, isolation_forest], default: iqr }
  threshold: { type: number, minimum: 0, default: 1.5 }
  group_by:  { type: array, format: column_selector, of: data, default: [] }
  seed:      { type: integer, default: 0 }
values:
  outlier_count: { type: integer }
grouping: { parameter: group_by }
seed: seed
gpu: supported
```

## Identity and versions

- `name` is an identifier ([Documents](01-documents.md)) and `version` an integer of at least 1. Workflows reference a node type as `name@version`.
- A published version MUST NOT change, its image included; any change to a node type produces a new version.
- Names form an open namespace: any publisher may define a node type under a name of its own, and a name carries no meaning to the platform, which reasons only about the contract. Names without a qualifier are reserved to built-in node types.

## Language and plan

`language` is the language of the node type's implementation: `python`, `sql` or `command`.

A node is a **plan** if and only if its code never receives data:

| Node | Plan | Who computes the result |
|---|---|---|
| `language: python`, `plan: ibis`: code that receives tables with a schema but no data or connection, and returns an Ibis expression over them | Yes | The engine the planner chooses: DuckDB in process, or a warehouse |
| `language: python`, `plan: polars`: code that receives Polars lazy frames over inputs that hold no data, and returns a lazy frame built from them | Yes | Polars, in process |
| `language: sql` | Yes, always | The engine the planner chooses; the query compiles through Ibis |
| `language: python` without `plan` | No: eager | The node's code |
| `language: command` | No: eager | The command-line tool, as a unit of its own |

A plan can be fused with its neighbors into one query or lazy plan, and its output schema derived before it runs. An Ibis or SQL plan can also be pushed down to a warehouse, and its memory class derived. An eager node runs as written. Python code that computes data itself, with Ibis, Polars or any other library, is eager. Column lineage does not depend on whether a node is a plan ([D59](../architecture/decisions/0059-column-lineage.md)).

`plan` MAY appear only with `language: python`. A reader MUST hold a node to its `plan`, whoever wrote the node-type document, by building the plan before any run:

- The builder receives only inputs that hold no data: unbound Ibis tables, or Polars lazy frames whose sources fail when read. Code that needs data therefore fails as it is built, and the reader MUST reject the node.
- The builder MUST return the kind of plan that `plan` names: an Ibis expression or a Polars lazy frame. Otherwise the reader MUST reject the node, stating what the builder returned.
- Every leaf of the returned plan MUST be one of the inputs given to the builder, which the derivation request names, or a constant that travels inside the compiled plan: a literal of an Ibis plan, or a frame held inside a serialized Polars plan. A table that an Ibis builder creates in memory compiles into a reference to a table registered in the builder's own session, and the reader MUST reject it ([D62](../architecture/decisions/0062-source-reads-and-publication.md)).
- A builder's result MUST depend only on the input schemas and parameter values, by which built plans are cached. A value that varies between runs, such as the time of the run, is passed as a parameter.
- A plan MAY call functions that run inside the engine, over columns or over batches of rows. The platform cannot analyze them, so each capability they hide degrades on its own: the columns they produce have task-level lineage, for example.
- A SQL node's query MUST parse and compile in its dialect.

A reader reports these errors when the node is edited and when the SDK generates the node type, so that none first appears in a run.

Plans are built only in the data plane, in units that receive schemas and parameter values but no data, credentials or network. The result is the plan's output schemas and its compiled plan, the query in the dialect of the engine chosen for it or the serialized lazy plan, with the expressions of its value outputs. A unit that runs the node runs the compiled plan and never calls the builder. Results are cached per tenant by node-type version and image, input schemas, parameter values and, for a compiled plan, its dialect. The control plane never runs a node's code.

`image` is `platform-base`, the platform's base image, or an image digest. `entry_point` is a Python callable written `module:function` for `python`, the query for `sql`, and an executable for `command`.

A node type whose plan compiles through Ibis, with `plan: ibis` or `language: sql`, lists in `dialects` the warehouse dialects it supports; DuckDB, the engine in process, is always supported. A Polars plan or an eager node type MUST NOT list dialects. `modes` lists the execution modes the node type supports, and is `[batch]`.

A node type states what its implementation can run on, never where it runs; the planner chooses, and a workflow may override the choice for a node among the engines the node is eligible for ([D57](../architecture/decisions/0057-node-type-contract.md)).

## Ports

`inputs` and `outputs` map port names, which are identifiers, to ports. A port's `type` is a format type, such as `tabular`.

- An input MAY be `optional`, and MAY accept `many` edges, which reach it in the order they are written.
- An output has a `schema` mode: `static`, `derived` or `dynamic`. The output schemas of plan nodes are derived; an output of an eager node is dynamic unless annotated.

The derived output schemas of plan nodes are computed when their plans are built, as described above.

## Parameters

`params` maps parameter names, which are identifiers, to parameter schemas. A parameter schema uses a profile of JSON Schema 2020-12 in which every construct has a counterpart among CEL's types:

| `type` | `format` | CEL type |
|---|---|---|
| `string` | | `string` |
| `string` | `date-time` | `timestamp` |
| `string` | `duration` | `duration` |
| `string` | `date` | `string`, holding a date |
| `integer` | | `int` |
| `number` | | `double` |
| `boolean` | | `bool` |
| `array` | | `list` of `items` |
| `object` | | `map` from string to `additionalProperties` |

The platform adds four formats:

| `format` | On | Meaning |
|---|---|---|
| `column` | `string` | One column of the input port named by `of` |
| `column_selector` | `array` | Columns of the input port named by `of`, selected by name, pattern or type ([D46](../architecture/decisions/0046-control-flow-constructs.md)) |
| `binding` | `string` | A logical name, bound to a resource per environment ([D41](../architecture/decisions/0041-ir-text-form-round-trip-and-structure.md)) |
| `secret` | `string` | A secret reference; expressions never see it ([D40](../architecture/decisions/0040-protocol-between-the-control-and-data-planes.md)) |

A column selector names which columns a node acts on; the columns of the input itself come from the upstream schema, never from the node type.

Besides `type`, and `format`, `of`, `items` and `additionalProperties` where the tables above use them, a parameter schema MAY state `enum`, `minimum`, `maximum`, `pattern`, `default`, `title` and `description`, and nothing else. A parameter without a `default` is required. An integer is accepted where a number is expected; a number is never accepted where an integer is expected.

### Values and expressions

A node in a workflow gives each parameter a fixed value or a CEL expression, and every value is held to the parameter's schema:

- A reader MUST check an expression's type against the parameter before any run.
- For a parameter with an `enum`, a reader MUST accept an expression only if every value it can produce is in the `enum`: a literal, a workflow parameter or value output whose own `enum` is a subset, or a conditional choosing between such values. It MUST reject any other expression.
- A reader MUST check every other constraint of a fixed value when the document is read, and of a computed value when the control plane evaluates it, before the unit starts. A node's code receives only values that satisfy its schema.

## Value outputs

`values` maps value-output names, which are identifiers, to schemas of the same profile, without the formats `column`, `column_selector`, `binding` and `secret`.

A plan node's value outputs are expressions over its plan, which derivation compiles with the plan and the unit that runs the node evaluates over its output; an eager node's code returns them. The row count of every output is available to expressions without being declared ([D63](../architecture/decisions/0063-python-node-sdk.md)).

## Execution properties

| Field | Meaning |
|---|---|
| `grouping: { parameter: <name> }` | The parameter that supplies the node's grouping key, by which the planner may repartition and fan out |
| `order: { parameter: <name> }` | The parameter that supplies the sort key on which the node's result depends; REQUIRED for a node whose result depends on order |
| `seed: <name>` | The parameter that seeds the node's randomness |
| `side_effects: { target: <name> }` | The `binding` parameter naming the external target of the node's side effect |
| `gpu` | `none`, the default, `supported` or `required` |
| `memory_floor` | Memory the implementation needs regardless of its data, such as `1Gi` |
| `memory` | A hint of the node's memory class: `streaming`, `blocking_spilling` or `blocking_non_spilling` |

A node with `side_effects` is never served from cache or fused, checks its lease and uses idempotency keys, and in a development run executes only if the run's environment binds its target itself.

The memory class of an Ibis or SQL plan is derived from its compiled query. Every other node's memory class is `blocking_non_spilling` unless `memory` states otherwise. A node type declares no other resource quantity; units are sized from estimates.

`title`, `description` and `tags` are for display and search only and never affect a node's meaning. `tags` lists distinct identifiers ([Documents](01-documents.md)), under which the palette groups and finds node types; their vocabulary is open.

## Code nodes

A code node runs a file under `code/` written in one of the languages and following an interface of that language: for Python, the interface described below under Python code ([D63](../architecture/decisions/0063-python-node-sdk.md)). A reader derives the node's contract, its inputs, outputs, value outputs and parameter schemas, and whether it is a plan, from the file's signature and annotations by static analysis, without executing it. A workflow therefore gives a code node only its file, its wiring and its parameter values. Annotations MUST be literal and map onto the parameter profile.

A `command` code node declares its contract in the workflow, and that declaration is its interface, since a command has no signature to analyze.

## Python code

Python node types, plugins and code nodes follow one interface ([D63](../architecture/decisions/0063-python-node-sdk.md), [D66](../architecture/decisions/0066-python-node-interface.md)). Every reader reads it from the source text without executing it and holds it to the same rules: the SDK, when it generates a node-type document or derives a plan, and the compiler, when it reads a code node.

```python
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Literal

import pandas as pd
from sdk import ColumnSelector, Grouping, Minimum, Seed, Value, node


@dataclass(frozen=True)
class Flagged:
    flagged: pd.DataFrame
    outlier_count: Value[int]


@node(version=1, title="Flag outliers", tags=["anomaly"], gpu="supported")
def outliers(
    data: pd.DataFrame,
    *,
    columns: Annotated[Sequence[str], ColumnSelector(of="data")],
    method: Literal["iqr", "zscore", "isolation_forest"] = "iqr",
    threshold: Annotated[float, Minimum(0)] = 1.5,
    group_by: Annotated[Sequence[str], ColumnSelector(of="data"), Grouping()] = [],
    seed: Annotated[int, Seed()] = 0,
) -> Flagged:
    """Flag rows whose values lie far from the rest.

    Args:
        columns: The columns to test.
        threshold: How far a value may lie before it is flagged.
    """
```

This is the code of the node type whose document opens this page, from which the SDK generates that document with the description and parameter descriptions added.

### Functions

A node is a module-level function decorated with the SDK's `node`. Every argument of the decorator MUST be a literal:

| Argument | Field |
|---|---|
| `plan` | `plan`: `"ibis"` or `"polars"`; absent for eager code |
| `version` | `version`; REQUIRED for a published node type |
| `title`, `tags` | `title`, `tags` |
| `gpu`, `memory`, `memory_floor`, `dialects` | the fields of the same names |

The node type's `name` is the function's name, and its `description` is the function's docstring without its `Args:` section. Code states no other field: the SDK's generator fills in `ir_version`, `kind`, `language`, `modes`, `entry_point`, which names the function's module and the function, and `image`. The decorator returns the function unchanged.

### Inputs

The parameters before `*` are the node's inputs, each named after its parameter, and the parameters after `*` are the node's parameters. A reader MUST reject a parameter before `*` that is not annotated with a table type, a table type after `*`, and `*args` or `**kwargs`. Inputs appear in the order written, and each has the port type `tabular`.

| Node | Table type of every input |
|---|---|
| `plan="ibis"` | `ibis.Table` |
| `plan="polars"` | `polars.LazyFrame` |
| Eager | `pyarrow.Table`, `polars.DataFrame` or `pandas.DataFrame`, chosen for each input |

An input annotated `T | None` with the default `None` is `optional`. An input annotated `Sequence[T]` accepts `many` edges, and is also `optional` when its default is `[]`.

### Parameters

A keyword-only parameter's annotation maps onto the parameter profile:

| Annotation | Parameter schema | The code receives |
|---|---|---|
| `str` | `type: string` | `str` |
| `int` | `type: integer` | `int` |
| `float` | `type: number` | `float` |
| `bool` | `type: boolean` | `bool` |
| `datetime.datetime` | `type: string`, `format: date-time` | an aware `datetime` in UTC |
| `datetime.timedelta` | `type: string`, `format: duration` | `timedelta` |
| `datetime.date` | `type: string`, `format: date` | `date` |
| `Literal[...]` of strings, or of integers | `enum` of the members, of their type | the member |
| `Sequence[T]` | `type: array`, `items` mapped from `T` | `list` |
| `Mapping[str, T]` | `type: object`, `additionalProperties` mapped from `T` | `dict` |

A reader MUST reject any other annotation, including unions, enumeration classes, `Literal` members of mixed types, floats or booleans, and classes with fixed fields.

A default MUST be a literal, or a `timedelta` or `date` built from literal arguments, and MUST satisfy the parameter's schema. A `datetime` parameter has no default. A parameter without a default is required.

Markers in `Annotated` add constraints and formats, each at most once on a parameter:

| Marker | On | Adds |
|---|---|---|
| `Minimum(n)`, `Maximum(n)` | `int`, `float` | `minimum`, `maximum` |
| `Pattern(p)` | `str` | `pattern` |
| `Column(of=...)` | `str` | `format: column` and `of` |
| `ColumnSelector(of=...)` | `Sequence[str]` | `format: column_selector` and `of` |
| `Binding()` | `str` | `format: binding` |
| `Secret()` | `str` | `format: secret` |
| `Title(t)` | any | `title` |

`of` MUST name an input of the same function that is required and accepts a single edge. A column selector's value reaches the code as the list of column names it selects. Constraint markers MAY also annotate the items of a sequence or the values of a mapping; format markers MUST NOT. A parameter's `description` is its entry in the `Args:` section of the function's docstring, written in the Google style.

A parameter that supplies an execution property carries a marker for that role. Each role marker MAY appear at most once in a function:

| Marker | On a parameter that is | Sets |
|---|---|---|
| `Grouping()` | a column or a column selector | `grouping: { parameter: <name> }` |
| `Order()` | a column or a column selector | `order: { parameter: <name> }` |
| `Seed()` | an `int` | `seed: <name>` |
| `SideEffectTarget()` | a binding | `side_effects: { target: <name> }` |

### Outputs

A function returns one table, an output class or `None`:

- A function annotated to return one table has one output, `data`.
- An output class is a dataclass declared with `frozen=True`. Each field annotated with a table type is an output named after the field, and each field annotated `Value[T]` is a value output, with `T` mapped as a parameter's annotation is, without the formats `column`, `column_selector`, `binding` and `secret`. A reader MUST reject a field of any other type, a field annotated `T | None`, a field with a default and a field of a sequence of tables.
- A function returning `None` has no outputs.

A plan returns its plan's table type, and its outputs are `derived`; eager code returns any of the eager table types, which the runtime converts to Arrow, and its outputs are `dynamic`.

### Names

A reader resolves the names in decorators and annotations through the module-level imports of the file, under any alias, including imports made only for type checking. It recognizes `node`, the markers and `Value` from `sdk`; `Annotated`, `Literal`, `Sequence` and `Mapping` from `typing`, and `Sequence` and `Mapping` from `collections.abc`; `datetime`, `timedelta` and `date` from `datetime`; `dataclass` from `dataclasses`; and the table types above from `ibis`, `polars`, `pyarrow` and `pandas`.

A type alias, written as a `type` statement, and an output class MAY be defined in the same file or in a module within the same root. The root is the directory on Python's import path: the `src` folder of a plugin package, or the `code/` folder of a project, with which a code node runs on its import path. A module `a.b` is the file `<root>/a/b.py` or `<root>/a/b/__init__.py`, and a relative import, where Python allows one, resolves against the package of the file that makes it. A reader follows such names from module to module and MUST reject a cycle. A reader MUST reject a name it cannot resolve in this way, a wildcard import, an annotation written as a string, a recognized name bound again in the module, and an alias written as an assignment.

### Errors

A reader MUST report every error in a file, not only the first, each with its file, line and column, the function and the parameter or field concerned, a code and a message. Codes are stable and shared by all readers, while each reader words its own messages. The conformance corpus holds node files, under `python/`, with the documents they MUST produce or the codes and locations of the errors they MUST produce.
