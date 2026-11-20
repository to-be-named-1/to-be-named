# 67. Shared IR schema package

Date: 2026-11-20
Applies to: platform.controlPlane, platform.unitRuntime, platform.derivationUnit

## Status

Accepted

Amends [56. IR documents and identifiers](0056-ir-documents-and-identifiers.md)
Amends [60. Code layout and tooling](0060-code-layout-and-tooling.md)

## Context

[D56](0056-ir-documents-and-identifiers.md) placed the schema in the control plane's authoring context, which embeds it, and gave the SDK the schema published with each release. The schema and its conformance corpus now have several readers: the control plane validates documents against the schema, the SDK writes node-type documents from it, and both the SDK's reader and the compiler's reader of code nodes are tested against the corpus ([D63](0063-python-node-sdk.md)). A Python package ships only files within it, and Go embeds only files within its package's folder.

## Decision

Where the IR schema and its conformance corpus live, and how the control plane and the SDK obtain the schema.

- **Location.** The schema and its conformance corpus live in a root-level folder, `ir/`, a contract shared by the control plane and the SDK, as `proto/` is.
- **Package.** The schema is one set of files, published as a Python package and a Go package, both named `ir`. The control plane embeds it through the Go package; the SDK depends on the Python package, so installing the SDK installs the schema of its release. The corpus is not part of the published package; the readers' tests read it from the repository.
- **Ownership.** The control plane remains the authority that validates documents against the schema ([D47](0047-control-plane-structure.md)); the schema's location makes no other container its owner.
- **Amends.** [D56](0056-ir-documents-and-identifiers.md): the schema is a shared package, which the control plane embeds and the SDK depends on. [D60](0060-code-layout-and-tooling.md): the folders include `ir/`.

## Consequences

- There is one copy of the schema, with nothing to synchronize.
- An SDK release carries the schema of its IR version through its dependency.

## Rejected alternatives

- A copy of the schema inside the SDK, checked against the source by a test. The repository would hold two copies.
- Copying the schema into the SDK when it is built. Every way of running the SDK would have to run the copy first.
- Leaving the schema inside the control plane's tree. Other readers would reach into another container's internal folder, which the code layout forbids for Go, and which no Python package can ship.

## Follow-ups

- The packages' names, with the product's name ([D60](0060-code-layout-and-tooling.md)).
