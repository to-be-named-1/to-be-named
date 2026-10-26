# AGENTS.md

Guidance for coding agents and new contributors working in this repository.

## The project

A workflow orchestration platform for data engineering, data science and machine learning: a visual canvas and a
text form in git over one intermediate representation (IR), a Go control plane, and Python execution units that
run in the customer's environment. The product is not named yet; `to-be-named`, `to-be-named-1` and the Python
package names `units` and `sdk` are placeholders. Do not invent a product name.

## Where the truth lives

- `docs/architecture/` is the only authoritative record of the architecture: the C4 model (Structurizr DSL),
  its documentation and the architecture decision records. Anything not recorded there is not decided.
- `docs/ir/` is the normative specification of the IR. Its schema and conformance corpus live in
  `controlplane/internal/authoring/ir/`.
- Read `docs/README.md` before changing anything under `docs/`; it states every convention and check.
- Code implements recorded decisions. If a change needs a design choice that is not recorded, stop and raise it
  instead of deciding it in code. Design proposals are written as decision sheets and recorded once confirmed.

## Layout

| Folder | Holds | Stream |
|---|---|---|
| `controlplane/` | Control-plane server; one package tree per bounded context under `internal/` | Backend |
| `agent/`, `cli/` | Data-plane agent and command-line interface | Backend |
| `internal/` | Go code shared between containers | Backend |
| `proto/` | Protobuf contracts | Shared |
| `units/` | Unit runtime and the units it runs | Data |
| `sdk/` | Python SDK: interfaces node code follows, generation of node-type documents and IR | Data |
| `webapp/` | Web application | Frontend |
| `tools/` | Scripts behind the documentation and IR checks | Shared |
| `docs/` | Architecture record and IR specification | Design |

Contracts (the IR schema and corpus, `proto/`) are shared: change both sides of a contract in the same pull
request, and add conformance cases with every schema change.

## Commands

| Command | Runs |
|---|---|
| `make go-check` | `go vet`, `go test`, golangci-lint (pinned image) |
| `make py-check` | `uv sync --locked`, ruff, pyright, pytest |
| `make docs-link` | Turns bare decision and open-item references in `docs/` into links |
| `make docs-check` | Structurizr validation and the documentation checks |
| `make ir-check` | The IR schema against its conformance corpus |
| `make check` | All of the above |

Run the checks for every area you touched before proposing a commit. Docker is required for the Structurizr,
IR and lint checks.

## Code conventions

- **Go.** One module at the root. Packages follow bounded contexts; never import another container's
  `internal/`. Tests use the standard library and go-cmp; the IR reader's tests are driven by the conformance
  corpus. Formatting and lint come from `.golangci.yml`.
- **Python.** A uv workspace (`units`, `sdk`), Python 3.14, src layout. ruff for lint and format, pyright for
  types, pytest for tests. Give test files unique names across packages. Node code reaches the runtime only
  through the interfaces in `sdk`, built-in node types included.
- **TypeScript.** Node 26, pnpm, React, Vite, TypeScript, Vitest and Biome, once the web application is
  scaffolded.
- **Comments only where needed.** Add a comment only when something is non-obvious: a reason the code cannot
  show, a constraint, a workaround or a surprising behavior. Do not restate what the code already says.
  Doc comments on exported Go identifiers and Python public APIs are the exception, since tools and readers
  rely on them.
- **No decision references in code.** Code, comments, configuration, package names and schemas never cite
  decision, open-item or capability IDs (such as "ADR 60" or "D18"). State the behavior or rule itself; a path
  into `docs/` is fine. Traceability lives in the documentation.
- Line endings are LF (`.gitattributes`); editors on Windows must not write CRLF.

## Documentation conventions (summary)

- Write bare IDs (`D57`, `S26`) and run `make docs-link`; never hand-write `{workspace}` links in prose.
- The documentation never names comparable software or compares the platform with it; technologies the
  platform uses or exports to may be named.
- No phasing outside the roadmap section, and no "for now" in decision text.
- An amendment rewrites the amended ADR in place and cites the amending ADR; a new choice is a new ADR.

## Git

- Commit messages are prefixed with the area, for example `docs: ...`.
- Keep it clean, no co-author trailers.
- Commit or push only when asked.

## Environment notes

- On Windows, Git Bash rewrites arguments that look like POSIX paths; the Makefile sets `MSYS_NO_PATHCONV=1`.
- Test Linux and Docker permission behavior in a Linux container, not on Docker Desktop for Windows.
