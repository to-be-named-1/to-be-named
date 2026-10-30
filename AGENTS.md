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
| `make go-check` | `go test`, golangci-lint (pinned image), whose standard linters include `go vet` |
| `make py-check` | `uv sync --locked`, ruff, pyright, pytest |
| `make web-check` | `pnpm install --frozen-lockfile`, Biome, `tsc`, Vitest, the Vite build |
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
- **TypeScript.** Node 26, pnpm, React, Vite, TypeScript, Vitest and Biome, in `webapp/`. Biome lints and
  formats (`pnpm --dir webapp format` applies its fixes), `tsc` checks types and Vitest runs the tests in jsdom.
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

- **Branches.** `main` holds the stable state and `dev` integrates work. Every change starts from an issue, on a
  short-lived branch from `dev` named `<type>/<issue>-<slug>`, such as `feat/21-ir-reader`;
  `gh issue develop 21 --base dev --name feat/21-ir-reader` creates it and links it to the issue.
- **Pull requests.** A work branch merges into `dev` through a pull request, usually squashed, so that the pull
  request's title becomes the commit message. Review and merging are left to the author's judgment; open a draft
  for work in progress.
- **Promotion.** `dev` is promoted to `main` at the end of each iteration, once verified, through a pull request
  merged with a merge commit. Never squash or rebase a promotion: `dev` would lack the commits it put on `main`,
  and every later promotion would conflict. A fix that cannot wait branches from `main` as `fix/<issue>-<slug>`
  and merges into `main`, which is then merged back into `dev`.
- **Keeping a branch current.** Rebase it onto `dev` and push with `--force-with-lease`, or merge `dev` into it
  when others share the branch. Never force-push `dev`, `main` or another person's branch.
- **Commit messages.** [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/), on one line:
  `<type>(<scope>): <description>`. Types: `feat`, `fix`, `docs`, `refactor`, `test`, `perf`, `build`, `ci`,
  `chore`, `style` and `revert`, the same as in branch names. The scope is optional: a top-level folder or a
  contract, such as `controlplane` or `ir`. `!` before the colon marks a breaking change to a contract. No
  co-author trailers.
- **Project status.** Move the issue to In Progress when its branch is created and to In Review when its pull
  request leaves draft. An issue is Done once its change is on `main`: the promotion pull request lists
  `Closes #<issue>` for every issue it carries, since GitHub reads the keyword only in pull requests into the
  default branch, and merging it closes them.
- **Release tags.** Once platform releases are versioned, each is tagged `v<version>` on `main`.
- Agents commit only on a work branch, never on `dev` or `main`, and commit or push only when asked.

## Environment notes

- On Windows, Git Bash rewrites arguments that look like POSIX paths; the Makefile sets `MSYS_NO_PATHCONV=1`.
- Test Linux and Docker permission behavior in a Linux container, not on Docker Desktop for Windows.
