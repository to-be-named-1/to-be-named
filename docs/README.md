# Documentation

This folder holds the formal documentation of the platform.

- [`architecture/`](architecture/workspace.dsl) is the architecture record: a C4 model written in the Structurizr DSL, its Markdown documentation and the architecture decision records (ADRs).
- Other formal documentation, such as the IR specification, sits beside it in a folder of its own and is linked from the architecture documentation.

## Viewing

| Command | Effect |
|---|---|
| `make docs-up` | Starts Structurizr local on <http://localhost:8080> (`STRUCTURIZR_PORT` overrides the port). It writes `architecture/workspace.json`, which is derived and never committed. |
| `make docs-down` | Stops it |
| `make docs-export` | Writes the workspace as JSON and as a static site to `docs/build/` (not committed) |
| `make docs-check` | Runs every check a commit must pass (below) |

The static site built by CI is attached to each run as the artefact `architecture-site`.

## Single source of truth

From the cut-over described below, `docs/architecture/` is the only authoritative record of the platform's architecture: the model, the documentation and the ADRs. Anything not recorded there is not decided. Until the cut-over, authority is held item by item, as the migration section sets out.

1. A decision is recorded only once confirmed, as a new ADR or as an amendment to one. The model and the documentation change in the same commit.
2. Proposals live in the workspace documentation's proposals section until confirmed; open questions live in its open-items section.
3. IDs are stable and never reused: decisions (D), open items (S) and capability lines (CORE, DE, DS, MLE). CORE 3.8 is unused.
4. Nothing temporary sits permanently on the diagrams or in the documentation. Temporary marking lives in removable overlays (diagrams) or in the roadmap section (documentation).
5. Every change passes `make docs-check` before it is committed; CI runs the same check.

## Migration from the design record

This section is temporary. It is removed in the commit that retires `project-design.md`.

- [`project-design.md`](../project-design.md) is frozen at revision v0.10 (11 October 2026) and is no longer edited.
- Until a decision's ADR is migrated, the design record remains the authority for that decision; the ADR stub says so. Once migrated, the ADR is the authority. New material goes only into `docs/architecture/`.
- The design record is retired when all fifty ADRs are migrated and reviewed, every part of the record has its destination, `python tools/docs/check.py --cutover` passes after a JSON export, and `make docs-check` is green. Its last commit is tagged `design-record-v0.10` and the file is then removed.

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
  ## Amendment history
  ## Follow-ups
  ## References
  ```

- Status is one word: **Accepted**; **Partial** (direction confirmed, details open); **Superseded**, with a `Superseded by` link; **Rejected**. Proposals are never ADRs.
- Links in the status block are labelled `Amends`, `Amended by`, `Supersedes` or `Superseded by`, and every link has its inverse in the other ADR.
- An amendment edits the amended ADR: an inline note where the change applies ("Amended 2026-10-11:" or "Amended 2026-10-11 by D51:"), an entry in its amendment history, and labelled links where another decision causes it. A decision is superseded only when it is replaced outright.
- References: a decision's references include the decisions, open items and capability lines it cites, the decisions that amend it, and the capability lines whose notes cite it. A decision that only cites another need not appear in the other's references.
- `Applies to` names model elements by identifier; each of them lists the decision in its `decisions` property, and the check confirms that both sides agree.
- Reasoning carried over from the design record's Part I §3 is cited in the Context section as "Reasoning item N".

### Model

- Files are included one by one, in a fixed order: people, external systems, the platform and its containers, relationships, deployment, overlays, then views. The DSL allows no forward references.
- One folder per container, `model/platform/<container>/`, holding `container.dsl` and the container's `docs/`.
- Identifiers are hierarchical and lowerCamelCase (`platform.controlPlane.runDriver`). View keys are explicit, kebab-case and prefixed by view type (`context`, `containers`, `components-control-plane`, `dynamic-…`, `deployment-…`).
- Relationship descriptions are present-tense verb phrases, unique between any pair of elements.
- Permanent tags: `External`, `Database`, `Web Browser`, `Maintenance unit`, `Leader only`, `Commercial`, `Extension point`, and on relationships `Asynchronous`. Properties: `decisions`, `roles`, `openItems`.
- Temporary content lives in overlays: one pair of files per concern, `model/overlays/<concern>.dsl` and `views/overlays/<concern>.dsl`, each opening with `// Overlay:`, `// Purpose:` and `// Remove when:` lines, each included by a single line in `workspace.dsl`.
- Diagrams use automatic layout; manual layout is not committed.

### Documentation

- Workspace documentation (`architecture/documentation/workspace/`) holds reference material: the brief, vocabulary, capability catalogue, open items, proposals, design agenda, implementation checklist, roadmap and revision history.
- Platform documentation (`architecture/documentation/platform/`) describes the architecture in arc42's twelve sections, in arc42's numbering.
- Container documentation follows one template: `01-responsibility`, `02-interfaces`, `03-components`, `04-state`, `05-key-flows`, `06-failure-and-scaling`, `07-security`, `08-configuration`, `09-decisions`. A section that does not apply is omitted; the numbering never changes.
- Each file begins with exactly one level-1 heading. Text refers to decisions, open items, capability lines and views by ID; relative links are checked.
- Documentation describes the target architecture and never says what is not yet built; phasing lives in the roadmap section only.
- Figures are text first; an image is an SVG or PNG beside its editable source. Diagrams are embedded with `![](embed:view-key)`.
- Register: neutral third person, British spelling.

### Checks

`make docs-check` validates the workspace with Structurizr, exports it as JSON and runs `tools/docs/check.py`, which checks:

1. ADR files: name, title number, date, status, labelled links and their inverses, section order.
2. `decisions` properties name existing ADRs and agree with each ADR's `Applies to` line.
3. No forbidden relationship, explicit or implied ([`tools/docs/forbidden-edges.json`](../tools/docs/forbidden-edges.json); each rule cites the decisions it restates).
4. Every overlay file carries its header.
5. Markdown headings and relative links.

`make docs-inspect` runs Structurizr's inspections and reports without failing, until the model is complete.
