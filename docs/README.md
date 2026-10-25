# Documentation

This folder holds the formal documentation of the platform.

- [`architecture/`](architecture/workspace.dsl) is the architecture record: a C4 model written in the Structurizr DSL, its Markdown documentation and the architecture decision records (ADRs).
- [`ir/`](ir/README.md) is the IR specification: the normative detail of the documents a project commits as IR. Its machine-readable schema and conformance corpus live with the code that owns them, in `controlplane/internal/authoring/ir/`. The specification is read on GitHub; Structurizr does not serve it, so the architecture documentation names it by its path.

## Viewing

| Command | Effect |
|---|---|
| `make docs-up` | Starts Structurizr local on <http://localhost:8080> (`STRUCTURIZR_PORT` overrides the port). It writes `architecture/workspace.json`, which is derived and never committed. |
| `make docs-down` | Stops it |
| `make docs-export` | Writes the workspace as JSON and as a static site to `docs/build/` (not committed); the static site holds the diagrams only |
| `make docs-check` | Runs every documentation check a commit must pass (below) |
| `make ir-check` | Checks the IR schema and its conformance corpus (below) |

The static site built by CI is attached to each run as the artifact `architecture-site`. The documentation and the decisions are read in Structurizr local, the primary reader.

The make targets run Structurizr as the host user, so that on Linux it can write its data directory and `docs/build`. Calling Docker Compose directly on Linux needs the same: `DOCS_UID=$(id -u) DOCS_GID=$(id -g) docker compose --profile docs up -d structurizr`.

## Single source of truth

`docs/architecture/` is the only authoritative record of the platform's architecture: the model, the documentation and the ADRs. Anything not recorded there is not decided. The IR specification, `docs/ir/`, states the normative detail of the IR's documents: it cites the decisions and never contradicts them, and where the two disagree the decision prevails until it is amended.

1. A decision is recorded only once confirmed, as a new ADR or as an amendment to one. The model, the documentation and the IR specification change in the same commit.
2. Proposals live in the workspace documentation's proposals section until confirmed; open questions live in its open-items section.
3. IDs are stable and never reused: decisions (D), open items (S) and capability lines (CORE, DE, DS, MLE). CORE 3.8 is unused.
4. Nothing temporary sits permanently on the diagrams or in the documentation. Temporary marking lives in removable overlays (diagrams) or in the roadmap section (documentation).
5. Every change passes `make docs-check` and `make ir-check` before it is committed; CI runs the same checks.

## Conventions

### Decisions

- ADRs use the adr-tools format: files `decisions/NNNN-kebab-case-title.md`, where `NNNN` is the decision number (ADR 47 is D47; new decisions continue after the last number).
- Template, with empty sections omitted and the order fixed:

  ```
  # 47. Control-plane structure

  Date: 2026-10-11
  Applies to: platform.controlPlane, platform.database

  ## Status

  Accepted

  Amends [8. Cache keying](0008-cache-keying.md)
  Amended by [50. Development mode](0050-development-mode.md)

  ## Context
  ## Decision
  ## Consequences
  ## Rejected alternatives
  ## Follow-ups
  ```

- Status is one word: **Accepted**; **Partial** (direction confirmed, details open); **Superseded**, with a `Superseded by` link; **Rejected**. Proposals are never ADRs.
- Links in the status block are labeled `Amends`, `Amended by`, `Supersedes` or `Superseded by`, and every link has its inverse in the other ADR.
- An amendment rewrites the affected text of the amended ADR in place, so that it always states the current decision, with no inline note or date; git history records when and how the text changed. A substantive change, a new choice with its own reasoning and rejected alternatives, is recorded as a new ADR, and both ADRs carry labeled links. A decision is superseded only when it is replaced outright.
- `Applies to` names model elements by identifier; each of them lists the decision in its `decisions` property, and the check confirms that both sides agree.
- Decisions recorded before this record began carry its start date, 2026-10-11. A new decision carries the date it is written, so dates never decrease as numbers rise: Structurizr orders the decision log by date, then by number, and the check enforces it.

### Model

- Files are included one by one, in a fixed order: people, external systems, the platform and its containers, relationships, deployment, overlays, then views. The DSL allows no forward references.
- One folder per container, `model/platform/<container>/`, holding `container.dsl` and the container's `docs/`.
- One file per deployment environment, `model/deployment/<environment>.dsl`. Deployment groups limit which instances the model's relationships connect, and traffic that reaches the control plane's roles through a Service or load balancer is drawn explicitly.
- Components are modeled only where a decision fixes them or a dynamic view needs them; finer structure is left to the code.
- Identifiers are hierarchical and lowerCamelCase (`platform.controlPlane.runDriver`). View keys are explicit, kebab-case and prefixed by view type (`context`, `containers`, `components-control-plane-execution`, `dynamic-…`, `deployment-…`).
- Relationship descriptions are present-tense verb phrases, unique between any pair of elements.
- Permanent tags: `External`, `Database`, `Object Storage`, `Web Browser`, `Maintenance unit`, `Leader only`, `Commercial`, `Extension point`, and on relationships `Asynchronous`. Properties: `decisions`, `roles`, `openItems`. `roles` names the control-plane roles that a component's actions require: `api`, `worker` and `candidate`, which are configured, and `leader`, which only the candidate that wins the election holds; `Leader only` marks exactly the components whose only role is `leader`.
- Temporary content lives in overlays: one pair of files per concern, `model/overlays/<concern>.dsl` and `views/overlays/<concern>.dsl`, each opening with `// Overlay:`, `// Purpose:` and `// Remove when:` lines, each included by a single line in `workspace.dsl`.
- Diagrams use automatic layout; manual layout is not committed.

### Documentation

- Workspace documentation (`architecture/documentation/workspace/`) holds reference material: the brief, vocabulary, capability catalog, open items, proposals, design agenda, implementation checklist and roadmap.
- Platform documentation (`architecture/documentation/platform/`) describes the architecture in arc42's twelve sections, in arc42's numbering.
- Container documentation follows one template: `01-responsibility`, `02-interfaces`, `03-components`, `04-state`, `05-key-flows`, `06-failure-and-scaling`, `07-security`, `08-configuration`, `09-decisions`. A section that does not apply is omitted; file numbers never change, while the section numbers Structurizr displays follow the files present. `03-components` gives each component a table row with its model description and, for a container deployed in roles, its actions by role; `09-decisions` lists the container's `decisions` property, each with what it settles for the container. Container documentation describes how the container behaves and cites the ADRs for the rules and their reasons; it never copies decision text.
- Each documentation file begins with one `##` heading, its section title; subsections use `###` and below. Structurizr hides `#` headings and numbers `##` sections in file order, so the platform documentation's files `01`–`12` carry arc42's numbering. ADRs keep `# N. Title`.
- References in prose use IDs as link text: `[D29](…)` to the ADR, `[S25](…)` to the open item, `[CORE 2.6](…)` to the capability line. Authors write bare IDs and run `make docs-link`, which adds the links; `make docs-check` reports any bare reference left. Open item S3 is linked by hand, because "S3" also names Amazon S3. On an ADR's status-block lines (`Amends`, `Amended by`, `Supersedes`, `Superseded by`) the link reads `N. Title`, matching the target's title; the linker writes and corrects that form, and the check enforces it.
- Links are written for Structurizr, the primary reader. Structurizr resolves a relative link only within one set: between ADRs, or between files of one documentation set. Each container's documentation is a set of its own. A link that crosses sets uses Structurizr's `{workspace}` form, such as `{workspace}/decisions/Platform#29`, `{workspace}/documentation#3.1` or, for a container's documentation, `{workspace}/documentation/Platform/Control-plane%20server#3`, with the container's name percent-encoded; it resolves in Structurizr and not on GitHub; the ID still reads correctly where a link does not resolve.
- Sections are addressed by the numbers Structurizr gives them: a set's files in name order, each file's `##` heading by its position, its `###` headings within it. An open item or capability line with a `###` heading of its own is linked to that heading, otherwise to its file's section. The numbers change as files are added, so `make docs-link` recomputes every link whose text is an ID, and rewrites a relative link into another set; `make docs-check` reports a link that crosses sets without the `{workspace}` form or names no section. Heading anchors derived from titles are never used.
- Documentation describes the target architecture and never says what is not yet built; phasing lives in the roadmap section only.
- Figures are text first; an image is an SVG or PNG beside its editable source. Diagrams are embedded with `![](embed:view-key)`.
- Register: neutral third person, American spelling.
- The documentation never names comparable software or compares the platform with it. Software the platform runs on, integrates with or exports to is named as technology.

### IR specification

- The specification is read on GitHub. Each file begins with one `#` heading.
- Its links are relative file links, never `{workspace}` links or heading anchors; `make docs-link` writes them from bare IDs, as in the architecture documentation.
- Normative statements use the BCP 14 key words (MUST, SHOULD, MAY), defined in its README.
- The other documentation conventions apply: American spelling, no phasing, no comparable software.
- The schema is JSON Schema 2020-12, one folder per IR version, without `$id`; the conformance corpus holds, per IR version, valid documents, documents the schema must reject (`invalid/schema/`) documents that break the YAML subset (`invalid/subset/`), which the compiler's tests check, and strings every writer must write back unchanged (`writer/strings.json`), which the writers' tests check.

### Checks

`make docs-check` validates the workspace with Structurizr, exports it as JSON and runs `tools/docs/check.py`, which checks:

1. ADR files: name, title number, date, status, labeled links and their inverses, section order, and dates that never decrease as numbers rise.
2. `decisions` properties name existing ADRs and agree with each ADR's `Applies to` line.
3. No forbidden relationship, explicit or implied ([`tools/docs/forbidden-edges.json`](../tools/docs/forbidden-edges.json); each rule cites the decisions it restates).
4. Every overlay file carries its header.
5. Markdown headings; relative links that resolve and stay within one set; `{workspace}` links that name an existing ADR or section; the text of links to ADRs; and, in the IR specification, relative file links without heading anchors.
6. No British spelling is used anywhere under `docs/` (the patterns are in `tools/docs/check.py`).
7. Roles and container documentation: a component is tagged `Leader only` exactly when its only role is `leader`; in a container's `03-components.md`, a table row that names one of its components gives the model's description in its second column, an `Actions by role` column labels exactly the component's `roles`, and every component has a row; `09-decisions.md` lists exactly the container's `decisions` property.
8. Deployment routing: in an environment with more than one control-plane instance, no web application, CLI or agent instance connects to a control-plane instance directly; traffic reaches the roles through a Service or load balancer, so a missing or misspelled deployment group fails the check.

It then runs `tools/docs/link.py --check`, which reports any reference not yet linked.

`make docs-inspect` runs Structurizr's inspections and reports without failing, until the model is complete.

`make ir-check` runs `tools/ir/check.sh` with `jv` in a container: for each IR version, every schema compiles, every valid document passes and every document under `invalid/schema/` fails.
