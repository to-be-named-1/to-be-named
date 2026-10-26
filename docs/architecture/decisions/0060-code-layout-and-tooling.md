# 60. Code layout and tooling

Date: 2026-10-26
Applies to: platform

## Status

Accepted

## Context

[D44](0044-minimum-technology-stack.md) chose the languages: Go for the control plane and the agent, Python for the unit runtime, React and TypeScript for the web application. [D47](0047-control-plane-structure.md) and [D54](0054-domain-driven-design.md) give each bounded context its own package tree. Frontend, backend and data work proceed in parallel, meeting at contracts that both sides change together: the IR schema, the protobuf contracts of [D40](0040-protocol-between-the-control-and-data-planes.md) and [D44](0044-minimum-technology-stack.md), node-type documents and the format of derivation ([D57](0057-node-type-contract.md)). Every contributor's first commit depends on where code lives and which tool versions check it.

## Decision

One repository holds every container's code, the contracts and the documentation, laid out by container, with each tool's version pinned in one place.

- **Repository.** One repository, so that a contract and both of its sides change in one commit.
- **Folders.** One per container with code: `controlplane/`, `agent/` and `cli/` in Go, each with `cmd/` and `internal/`; `units/` and `sdk/` in Python; `webapp/` in TypeScript. Go code shared between containers lives in `internal/` at the root, protobuf contracts in `proto/`, the checks' scripts in `tools/` and the documentation in `docs/`.
- **Go.** One module at the root, `github.com/to-be-named-1/to-be-named`; Go's rule on `internal` packages keeps containers from importing one another's internals. The control plane's packages form one tree per bounded context under `controlplane/internal/<context>/` ([D47](0047-control-plane-structure.md), [D54](0054-domain-driven-design.md)). Go 1.27, with the toolchain fixed exactly in `go.mod`. Tests use the standard library and go-cmp; golangci-lint v2 runs its standard linters with errorlint and misspell in the US locale, and gofmt and goimports as formatters.
- **Python.** CPython 3.14, one version per base image ([D44](0044-minimum-technology-stack.md)). A uv workspace at the root with two members, `units` and `sdk`, and one lockfile; `units` depends on `sdk`, whose interfaces node code follows, and each kind of unit is an entry point of `units`. ruff lints and formats, pyright checks types and pytest runs the tests.
- **TypeScript.** Node 26, the long-term support release; pnpm, its version fixed in `package.json`; React 19, Vite 8 and TypeScript 7; Vitest for tests; Biome for lint and format.
- **Pinned versions.** A tool's version is fixed by its own lockfile or toolchain line where it has one (`go.mod`, `uv.lock`, the pnpm lockfile), and otherwise by an exact image tag in `docker-compose.yml`: golangci-lint, Structurizr and jv. `make go-check`, `make py-check` and `make check` run the same checks locally and in CI, where each stack has a workflow limited to its paths.
- **Names.** The control plane's and the agent's binaries are `controlplane` and `agent`. The CLI's command and the Python packages' names follow the product's name, and the module path follows the organization's.

## Consequences

- Renaming the organization changes the module path and every Go import, in one search and replace.
- Each stream can begin with the conventions in place, against fakes of the contracts it does not own.
- The check that the control plane's package trees match its component groups can cite this layout.

## Rejected alternatives

- A repository per stream or per container. A contract and both of its sides could not change in one commit, and the IR corpus and protobuf files would be copied between repositories.
- A Go module per container, joined by a workspace. Nothing is released as a separate library, and separate modules would version the shared contracts apart.
- An assertion library for Go tests. The standard library with go-cmp's diffs covers the same needs without a further dependency.
- mypy. pyright checks the same annotations and is faster in editors.
- npm. pnpm resolves dependencies strictly and installs faster.
- ESLint with Prettier. Two tools and two configurations, where Biome is one.
- Installing golangci-lint with `go install` or as a Go tool dependency. Its maintainers support only the released binaries and image, since a local build depends on the local Go version and can alter the project's dependencies.

## Follow-ups

- The names of the CLI's command and of the Python packages, with the product's name.
- Generating code from protobuf, with the first contract.
- Building the units' images, with the image builder and registry (technology table).
