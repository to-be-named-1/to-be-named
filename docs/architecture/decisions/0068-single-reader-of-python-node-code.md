# 68. Single reader of Python node code

Date: 2026-11-23
Applies to: platform.controlPlane

## Status

Accepted

Amends [44. Minimum technology stack](0044-minimum-technology-stack.md)
Amends [60. Code layout and tooling](0060-code-layout-and-tooling.md)
Amends [63. Python node SDK](0063-python-node-sdk.md)
Amends [66. Python node interface](0066-python-node-interface.md)
Amends [67. Shared IR schema package](0067-shared-ir-schema-package.md)

## Context

[D63](0063-python-node-sdk.md) and [D66](0066-python-node-interface.md) gave Python node code two readers: the SDK, which generates node-type documents, derives plans and backs its testing module, and the compiler, which reads a project's code nodes. The rules they apply are many and fine-grained, from names resolved across the modules of a root to defaults evaluated from literals and errors located to the byte, and a shared corpus finds a disagreement only where it holds a case. The reader must be written in Python, since authors test their node code without the platform. The control plane is written in Go ([D44](0044-minimum-technology-stack.md)), and untrusted code runs only in the data plane ([D21](0021-architecture-planes.md)); reading code with Python's parser executes none of it. Reading needs only Python's standard library, while the SDK depends on Arrow and holds derivation and execution. Node code shares its Python environment with the runtime and with the libraries its authors bring ([D65](0065-unit-specification-and-agent-unit-contract.md)). A control plane serves many projects, and in a hosted deployment many tenants, so one file that is slow or costly to read must not hold up other compiles.

## Decision

How the compiler reads Python code nodes, where the reader lives, under which version of the interface's rules, and within which limits.

- **One reader.** The reader of Python node code is the only one. It is a package of its own, which uses only Python's standard library. The SDK depends on it and re-exports it, so that the SDK's generator and testing module, and authors, reach it through the SDK; the compiler reads code nodes through it.
- **Layout.** `ir/` holds the IR schema in `ir/schema/`, the reader in `ir/reader/` and their conformance corpus in `ir/conformance/`. In Python the two packages share the namespace `ir`, as `ir.schema` and `ir.reader`, so that neither takes a top-level name that a library brought by node code could also take; the schema's Go package is `schema`.
- **Worker.** The control plane's image holds a Python runtime and the reader alone. The server runs the reader in a worker process that it starts, starts again when the worker fails and ends when a request exceeds a limit; the worker belongs to the server's container and is not a service of its own. The server and the worker exchange JSON lines over the worker's standard input and output: a request carries the files of the root, the paths to read and whether to read them as node types or as code nodes, and a response carries the contracts read and the errors found. The worker reads neither storage nor the network, and keeps nothing between requests.
- **Versions.** The rules of the Python interface belong to an IR version, as the IR specification states them, and change only with a new IR version. A code file is read under the IR version of the workflow document that refers to it. The worker reads every IR version in the control plane's window, and the contract of a code node read under an older version is migrated as documents are. The compiler checks that the image a code node runs in supports that IR version.
- **Limits.** The server bounds each request from outside the worker: its time, the worker's memory, the size of each file and of the request, and the number of workers are settings, with defaults of 5 seconds, 256 MiB, 1 MiB, 10 MiB and one worker. A request that exceeds its time or memory ends the worker, which the server starts again, and the compile reports an error with a stable code; the worker reports code nested too deeply to read in the same way. The worker has no sandbox beyond the container's isolation, since it parses code and never executes it.
- **Amends.** [D44](0044-minimum-technology-stack.md): the control plane's image holds a Python runtime for the reader of node code. [D60](0060-code-layout-and-tooling.md): the workspace holds `ir/schema` and `ir/reader`. [D63](0063-python-node-sdk.md): the reader of Python node code is a package that the SDK depends on, and reads for the SDK and for the compiler. [D66](0066-python-node-interface.md): one reader reads the interface, and the corpus tests it. [D67](0067-shared-ir-schema-package.md): the schema lives in `ir/schema/`, published as `ir.schema` and as the Go package `schema`.

## Consequences

- A file reads the same for the SDK and for the compiler, since both run the same reader.
- The control plane's image carries a Python runtime and the reader, which depends on no other package, and takes the runtime's security updates; it carries neither the SDK nor the SDK's dependencies.
- Authors reach the reader through the SDK and never install it on its own.
- The control plane's tests that compile code nodes need Python.
- An author's installed SDK may be older or newer than the control plane's; the compiler's reading is the one that counts.
- The reader keeps the rules of every IR version in the control plane's window.

## Rejected alternatives

- A second reader in Go, in the compiler. Two implementations of the same fine-grained rules would drift wherever the corpus has no case, and every change to the interface would be made twice.
- Python compiled to WebAssembly and run inside the server's binary. It would keep one binary and sandbox the parser, but it depends on a WebAssembly build of each Python release, with a start-up time and size that nothing measured supports.
- Reading code nodes in the data plane, where Python already runs. Showing a code node's ports while authoring would wait on a reachable agent.
- One reader in Go that the SDK calls as a bundled program. It would replace the Python reader that authors' tests use, and the SDK would ship a native program for each platform.
- Contract files that the SDK writes for each code node and the compiler reads. They go stale whenever code changes without them, and a code node edited on the canvas still needs a reader on the server.
- A worker for each SDK version that projects or images pin. Each would be another environment to ship and patch, and the versions would disagree as two readers do.
- Limits enforced inside the worker. A regular expression matched in native code cannot be interrupted from within its process; only ending the process stops it.
- The reader inside the SDK. The control plane's image would carry the SDK and its dependencies, Arrow among them, for code it never runs.
- The SDK's dependencies made optional, so that the control plane could install the SDK alone. Every author and plugin package would then need an extra for what testing node code always needs.
- The reader inside the schema's package. The schema is published alike for Go and for Python, and the Go package would have no reader.
- Top-level packages named `schema` and `reader`. They would share an environment with node code, where names that generic clash with the libraries authors bring.

## Follow-ups

- How an image states the IR versions it supports, with the platform's images.
