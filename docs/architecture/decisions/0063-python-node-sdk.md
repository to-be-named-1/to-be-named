# 63. Python node SDK

Date: 2026-11-04
Applies to: platform.controlPlane, platform.unitRuntime, platform.derivationUnit, platform.probeUnit

## Status

Accepted

Amends [41. IR text form, round-trip and structure](0041-ir-text-form-round-trip-and-structure.md)
Amends [57. Node-type contract](0057-node-type-contract.md)
Amends [60. Code layout and tooling](0060-code-layout-and-tooling.md)

## Context

[D57](0057-node-type-contract.md) left to the SDK the interface that Python node code follows. The compiler derives a code node's contract from its file by static analysis, without executing it; the SDK generates the node-type documents of built-in node types and plugins; and node code reaches the runtime only through the SDK. Built-in node types follow the same path as plugins ([D57](0057-node-type-contract.md), [D58](0058-behavior-follows-properties.md)), so they cannot be part of the runtime that calls them. Plan nodes never receive data, so their value outputs cannot be values their builders compute. Compiling Ibis expressions needs no DuckDB, and running compiled SQL needs none of Ibis's backends, while Ibis's own DuckDB backend supports only some DuckDB releases.

## Decision

The interface that Python node code follows, how node-type documents are produced from it, where derivation and execution are implemented, where the platform's own node types live, and which libraries each part needs.

- **Functions.** A Python node type, plugin or code node is a module-level function marked by the SDK's `node` decorator, whose arguments are literals and state whether the function returns a plan, `plan="ibis"` or `plan="polars"`, or is eager. The compiler and the SDK read the decorator, the signature and the annotations without executing the code ([D57](0057-node-type-contract.md)).
- **Inputs.** A parameter annotated with a table type is an input port named after the parameter: an Ibis table for an Ibis plan, a Polars lazy frame for a Polars plan, and for eager code an Arrow table, a Polars data frame or a pandas data frame, into which the runtime converts its Arrow input. An input annotated as optional, with `None` as its default, is optional; an input annotated as a list accepts several edges.
- **Parameters.** Keyword-only parameters, with literal annotations and defaults, are the node's parameters, mapped onto the parameter profile ([D57](0057-node-type-contract.md)): strings, integers, numbers, booleans, lists, `Literal` for an enum, date-times and durations. Constraints and the platform's formats are markers in `Annotated`, such as a minimum, a column or columns of a named input, a binding or a secret.
- **Outputs.** A function that returns one table has one output port, `data`. A function with several outputs returns a class declared with typed fields: fields typed as tables are output ports, and fields typed as values are value outputs.
- **Value outputs.** A plan node's value output is an expression over its plan, an Ibis scalar or a Polars expression, which derivation compiles with the plan and the execution unit evaluates over the node's output once it is computed; an eager node returns the value itself. A DuckDB segment ends at a node with value outputs unless the node's output is stored anyway, while a Polars plan computes a table and its values in one pass. The row count of every output is available to expressions without a declaration ([D41](0041-ir-text-form-round-trip-and-structure.md)).
- **Documents.** The SDK generates a node type's document from its code and builds its plan on inputs that hold no data, reporting the errors of [D57](0057-node-type-contract.md). Generated documents are marked as generated ([D58](0058-behavior-follows-properties.md)). A node-type document may also be written by hand, as those of SQL and command node types are, and is held to the same checks. For Python node types, CI generates the documents again and fails where one differs from the document committed.
- **Derivation and execution in the SDK.** Building a plan on inputs that hold no data, checking it, compiling it with its value outputs, binding a compiled plan to its inputs, running it and evaluating its values are functions of the SDK. The derivation and execution units call them, and add only what running as a unit needs: the unit specification, the agent, staging, commits and logs. The SDK's testing module calls the same functions, so that a node type's tests build and run it as the platform does, without an agent.
- **Connectors.** The SDK defines the reader interface of connectors, `probe`, `schema` and `open` ([D62](0062-source-reads-and-publication.md)), and the probe and execution units call connectors through it.
- **The platform's node types and connectors.** The node types and connectors that the platform publishes live in a package of their own, which depends only on the SDK and is installed in the platform's base image as a plugin would be; the entry points of its node types' documents name its functions. The runtime loads node code only through a node-type document's entry point: the runtime's package never imports the package of node types, nor that package the runtime's, and the linter checks both.
- **Dependencies.** The SDK depends on Arrow, with Ibis and Polars as optional extras. Derivation needs Ibis and its SQL compiler but no DuckDB; execution needs DuckDB, Arrow and Polars but none of Ibis's backends; serialized Polars plans need cloudpickle wherever they are written or read. Images pin exact versions, and the base image ships a DuckDB release that its pinned Ibis release supports, since authors' eager code may use Ibis on DuckDB. The runtime's own code uses only DuckDB interfaces present in every release an image may pin.
- **Amends.** [D41](0041-ir-text-form-round-trip-and-structure.md): a plan node's value outputs are expressions over its plan, and every output's row count is available to expressions. [D57](0057-node-type-contract.md): value outputs of plan nodes, the interface that Python code files follow, and hand-written node-type documents held to the same checks. [D60](0060-code-layout-and-tooling.md): the workspace gains the package of the platform's node types, and the SDK implements derivation and execution.

## Consequences

- Authors of plugins and code nodes test against the platform's own derivation and execution without installing the runtime.
- Upgrading Ibis changes the base image and therefore produces new versions of the platform's node types ([D27](0027-ibis-for-relational-node-definitions.md)).
- A Python node type's code and its document cannot drift apart unnoticed.

## Rejected alternatives

- Classes, or functions found by a naming convention. A decorator states plan or eager where a static reader finds it, and lets a module hold helper functions.
- The platform's node types inside the runtime's package. They would ship with the runtime rather than as versioned node types, and could reach the runtime's internals, which a plugin cannot.
- A package per node type. Packaging and distribution are open ([S26]({workspace}/documentation#7.25)), and one package versions its node types together with the base image that holds them.
- Value outputs only for eager nodes. A metric over a plan's output would need an eager node holding the data in memory.
- Derivation and execution implemented in the runtime, with the testing module depending on it or copying it. Authors would install the runtime to test their nodes, or tests would pass where the platform fails.
- Only generated node-type documents. SQL and command node types have no signature to generate them from.

## Follow-ups

- How expressions name the row counts of outputs, with the expression environment (design agenda).
- How a connector is referenced and loaded, with plugin identity and distribution ([S26]({workspace}/documentation#7.25)) and the manifest of plugins ([D18](0018-format-types-plugin-implementations-and-bindings.md)).
- The names of the packages, with the product's name ([D60](0060-code-layout-and-tooling.md)).
