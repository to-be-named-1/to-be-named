# to-be-named

A workflow orchestration platform for data engineering, data science and machine learning. The product is not
named yet; the repository and organization names are placeholders.

The architecture is recorded in [`docs/architecture/`](docs/architecture/workspace.dsl) and the IR specification in
[`docs/ir/`](docs/ir/README.md); [`docs/README.md`](docs/README.md) describes both and their conventions, and the decisions behind the code
layout and tooling are recorded there.

## Layout

| Folder | Holds | Language |
|---|---|---|
| `controlplane/` | Control-plane server: one package tree per bounded context under `internal/` | Go |
| `agent/` | Data-plane agent | Go |
| `cli/` | Command-line interface | Go |
| `internal/` | Go code shared between containers | Go |
| `proto/` | Protobuf contracts | Protobuf |
| `units/` | Unit runtime and the units it runs | Python |
| `sdk/` | Python SDK | Python |
| `webapp/` | Web application | TypeScript |
| `tools/` | Scripts behind the documentation and IR checks | Python, shell |
| `docs/` | Architecture record and IR specification | Markdown, Structurizr DSL |

## Development

Prerequisites: Git, Docker, [Go](https://go.dev/dl/) (any recent version; `go.mod` fetches the exact toolchain),
[uv](https://docs.astral.sh/uv/) (it installs Python 3.14 itself), Python 3 for the documentation scripts, and
GNU Make.

| Command | Runs |
|---|---|
| `make go-check` | `go vet`, `go test` and golangci-lint |
| `make py-check` | `uv sync --locked`, ruff, pyright and pytest |
| `make docs-check` | Structurizr validation and the documentation checks |
| `make ir-check` | The IR schema and its conformance corpus |
| `make check` | All of the above |
| `make help` | Every target |

Pinned image tags live in `docker-compose.yml`; tool versions otherwise come from `go.mod`, `uv.lock` and
`.python-version`. CI runs the same targets, one workflow per stack, on changes to that stack's files.
