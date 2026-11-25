# 66. Python node interface

Date: 2026-11-19
Applies to: platform.webApp, platform.controlPlane, platform.unitRuntime, platform.derivationUnit

## Status

Accepted

Amends [63. Python node SDK](0063-python-node-sdk.md)
Amended by [68. Single reader of Python node code](0068-single-reader-of-python-node-code.md)

## Context

[D63](0063-python-node-sdk.md) chose the shape of the Python interface: decorated functions read statically, parameters typed as tables as inputs, keyword-only parameters with markers in `Annotated`, output classes and `Value[T]`. It left their exact form open. One reader reads that form, for the SDK, which generates node-type documents and derives plans, and for the compiler, which reads code nodes ([D68](0068-single-reader-of-python-node-code.md)); it never executes the code, so every rule must be decidable from the source text alone. Node code shares its environment with the runtime and with the libraries its authors bring ([D65](0065-unit-specification-and-agent-unit-contract.md)). The palette and the canvas's forms read node-type documents ([D57](0057-node-type-contract.md)), including fields that never affect a node's meaning.

## Decision

The exact form of the Python interface: what the decorator, the markers, the annotations and the output classes carry, how readers resolve names and report errors, and how node types are labeled for display. The normative detail is in the IR specification, `docs/ir/03-node-types.md`.

- **Decorator.** The `node` decorator takes only literal arguments: `plan`; the version of a published node type; an optional title and tags; and the execution properties of the node as a whole, its GPU use, memory floor, memory hint and dialects. The node type's name is the function's name and its description the function's docstring. The decorator returns the function unchanged: node types are found through the entry points their documents name and checked by the readers, never when a module is imported. The SDK's generator fills in the fields that code does not state: the document's constants, the entry point and the image.
- **Node types and code nodes.** A reader reads code either as node types, as the SDK's generator does for a plugin, or as code nodes, as the compiler does for a project's code folder. The arguments that only node types state are held to their rules when code is read as node types, and are ignored when it is read as code nodes, so that a node type's file reads unchanged as a code node.
- **Markers.** Each marker is an immutable object with literal arguments, and stands for one construct of the parameter profile ([D57](0057-node-type-contract.md)): a minimum, a maximum or a pattern; a column or a column selector of the input that its `of` names, which is always stated and names a required input with a single edge; a binding; or a secret. The parameter that supplies a node's grouping key, sort key, seed or side-effect target carries a marker for that role, which a reader accepts only on a parameter of the matching kind, and at most once per function. A parameter's description comes from the function's docstring, written in one documented style, and an optional marker gives its title.
- **Types.** Strings, integers, numbers, booleans, date-times, durations and dates map onto the parameter profile, `Literal` onto an enumeration of strings or of integers, and the read-only types `Sequence` and `Mapping` onto arrays and maps. A date-time parameter receives an instant in UTC. A default is a literal, or a duration or date built from literals; a date-time parameter has no default. Unions, enumeration classes and classes with fixed fields are rejected.
- **Inputs.** Inputs precede the keyword-only parameters. A plan's inputs all have its plan's table type, while eager code chooses a type for each input, into which the runtime converts its Arrow input. An input with several edges is annotated as a sequence, and is optional when it has a default.
- **Outputs.** A function returns one table, an output class or nothing. An output class is a frozen dataclass whose fields are tables or `Value[T]`, with `T` in the parameter profile without the platform's formats. Its fields are fixed: none is optional or has a default.
- **Tags.** A node type may carry tags, distinct identifiers that the palette shows and searches. They never affect a node's meaning, and their vocabulary is open.
- **Names.** A reader resolves names through the module's imports, under any alias, and through type aliases and output classes defined in the same file or in a module within the same root. The root is the directory on Python's import path, the source folder of a plugin package or the code folder of a project, with which a code node runs on its import path; a module's name maps onto a file or a directory under the root as Python maps it, and relative imports resolve as Python resolves them. A name from anywhere else, other than the libraries the interface recognizes, cannot be read and is rejected.
- **Errors.** A reader reports every error in a file, each with its location, the node and parameter or field concerned, a stable code and a message. The reader is tested against a corpus of node files with their expected documents and errors, compared by code and location ([D68](0068-single-reader-of-python-node-code.md)).
- **Amends.** [D63](0063-python-node-sdk.md): an input with several edges is annotated as a sequence, and readers follow type aliases and output classes into modules within the same root.

## Consequences

- A file that the SDK reads is a valid code node for the compiler, and the reverse, since both read it with the same reader ([D68](0068-single-reader-of-python-node-code.md)).
- A change to a type alias that several node types share changes each of their documents, and each needs a new version ([D57](0057-node-type-contract.md)); generating the documents again in CI shows every one of them.
- Node signatures hold defaults that are mutable objects, such as an empty list for a sequence. This is safe, since the runtime always passes every value.
- The interface adds no library to the environment that the SDK shares with node code.

## Rejected alternatives

- Decorator arguments naming the parameters that supply a grouping key, a sort key, a seed or a side-effect target. A name in a string drifts from the parameter it names, while a marker sits on the parameter itself.
- A fixed set of categories. A broad category such as transformations would hold most node types and help neither browsing nor search, and a fixed set imposes one taxonomy on every plugin. Having no display field at all would leave search to names and descriptions.
- Enumeration classes. Readers would read class bodies, the code would name members while documents hold values, and the runtime would convert each value; a type checker already holds a `Literal` to its values.
- `list` and `dict` annotations. They would state that node code may change the values of its parameters.
- Output classes as models of a validation library. The library would be pinned in every image beside the version an author's code needs, and its validation finds nothing to check in tables and plan expressions. Named tuples invite outputs confused by position.
- A decorator that registers node types or checks its arguments when a module is imported. It would be a second way of finding node types and a second checker, which could disagree with the readers.
- Reading only the node's own file. Shared enumerations and output classes would be copied, and the copies would drift apart.
- Evaluating annotations by importing the module. Reading would run node code, which runs only in the data plane ([D21](0021-architecture-planes.md)).
- Telling node types from code nodes by what their code states. A node type that omits a required argument would silently read as a code node, and the error would surface later and without a location.
- Rejecting, in code nodes, the arguments that only node types state. A node type's file would need edits before it could serve as a code node.

## Follow-ups

- The values that node code receives at run time for bindings and secrets.
- Static output columns of eager nodes, with the dataset declarations (design agenda).
- Outputs whose number depends on a parameter's value, such as the parts of a split, with split semantics ([DS 2.8]({workspace}/documentation#5)).
- How node code declares execution modes other than batch, with streaming ([D6](0006-streaming.md), [D12](0012-streaming-readiness.md)); the readers give every node type the mode batch.
