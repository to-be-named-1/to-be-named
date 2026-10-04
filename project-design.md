# Reproducible Workflow Orchestration Platform — Project Reference

> **Status: working draft. Nothing in this document is final.**
> Every decision, design, capability statement and example recorded here reflects the state of the discussion at the time of compilation. All of it is provisional and may change as development proceeds and as implementation experience, measurements and user feedback come in. "Decided" in the decision log means agreed for now, not fixed.

This document has three parts:

- **Part I · Project details.** What the platform is, supplementary vocabulary, the reasoning behind key decisions and rejected alternatives, technology choices, and conventions for maintaining the record.
- **Part II · Capability catalogue.** The full catalogue: overview, key terms, architecture, worked engine examples, dataset lifecycle, decision log D1–D39, open items S1–S24 and every capability line. Diagrams are not reproduced; each figure is replaced by a description of what it shows, and the drawings are in the illustrated catalogue.
- **Part III · What remains to be discussed.** Proposals not yet confirmed, conditions and deferred follow-ups attached to decisions, open items, the pre-development triage, and the remaining design agenda.

---

# Part I · Project details

## 1. The project in brief

A cloud-based, **open-core**, **domain-agnostic** web platform for assembling, scheduling, executing and monitoring multi-stage data and computation pipelines, with **reproducibility as a first-class, verifiable product capability**.

- **Authoring.** Pipelines are built on a visual canvas and compiled to a custom intermediate representation (IR), which is the single source of truth. Definitions round-trip to text (YAML or Python) in git.
- **Execution.** Containerised execution units run on Kubernetes, HPC clusters (Slurm, through outbound agents), cloud batch, or a single-machine container deployment. Relational work is pushed down to the customer's warehouse where the data lives.
- **Deployment model.** Bring-your-own-compute is the primary model: execution runs on the customer's own infrastructure and the vendor hosts only the interface and control planes (D22). Hybrid and self-hosted are the first-class topologies; fully managed serves trials and small teams.
- **Processing engines.** Built-in tabular nodes are defined as Ibis expressions and run on DuckDB in-process or are pushed down to Postgres or Snowflake, with Polars used only by justified exception and for code nodes; non-tabular work runs in Python or container-command runtimes and scales by fan-out (D25, D27). The planner checks each unit's estimated working set against backend capacity rather than relying on declared dataset sizes (D34).
- **Disciplines served.** Data engineering, data science and ML engineering, on one shared substrate (CORE). Bioinformatics and sequence analysis is the **demonstration domain**, not a specialisation.
- **First slice.** Development begins with the tabular family only, on the single-machine container deployment and Kubernetes, with Ibis on DuckDB in-process (Polars by justified exception and for code nodes), the visual canvas and git round-tripping; execution is driven by a pull-based agent in every deployment, and tenant and project isolation is enforced throughout from the start (D29, D30). Warehouse pushdown, the other dataset families, HPC and cloud batch follow.
- **Excluded for now.** Deep learning and visual neural-network design; a native streaming runtime (batch first, then micro-batch, with streaming seams preserved); container-free local execution; online model serving; a platform-run Spark engine.
- **Positioning.** "The n8n of data engineering, data science and MLE", with production orchestration semantics (logical intervals, backfills, fan-out, retries, fair scheduling) and verifiable reproducibility. The closest existing product is Dataiku DSS, whose bring-your-own-compute model and cross-location behaviour the design now follows.
- **Principle.** Standard data-engineering practice comes first; reproducibility and its constraints are opt-in, never imposed (D36).
- **Vision.** Large-scale analysis should be reproducible by construction. Every run carries complete provenance and a verified statement of how closely it can be reproduced.
- **Business model.** Open core. The core is open source; managed cloud, multi-tenancy, enterprise support and AI assistance are paid. The licence and the exact open/paid line are deferred (D5).

## 2. Supplementary vocabulary

Terms used throughout that are not given their own card in the catalogue's Key terms.

| Term | Meaning |
|---|---|
| Task run, attempt, run trace | One execution of a unit is a task run (a map makes many); each try is an attempt; the run trace records them all and is always acyclic because loops are unrolled. |
| Canonicaliser vs comparator | A canonicaliser normalises an output so it can be hashed exactly, with no tolerance; a comparator judges whether two outputs are the same result within a tolerance and explains the verdict. |
| Managed vs external dataset | Distinguished by who owns the lifecycle, not by where the bytes sit. |
| Partition vs version | A partition is a slice of the key space; a version is state over time. A snapshot reuses untouched partition versions. |
| Open partition | A partition appended to by successive runs until explicitly marked complete. |
| Partition dependency function | How output partitions depend on input partitions: identity, time window, all, latest, specific values, or discovered at run time by a merge node. |
| Dataset family | A group of formats that behave alike on the platform (tabular, semi-structured, text and documents, images, genomics, ML artifacts). |
| Format type, plugin, binding | The platform defines a format type (for example `genomics/bam` v1); plugins implement types; each dataset is bound to one pinned implementation. |
| Materialisation request | A declarative request to make a dataset current through a given time, for which the reconciler plans the minimum work. |
| Engine segment | Consecutive in-process nodes on the same engine, chained so that one optimiser sees them all. The level between node and execution unit (D32). |
| Phase and outcome | Every run, task run and attempt carries a lifecycle phase (pending, active, suspended, ended) and, separately, an outcome that is empty until the phase is ended (D31). |
| Checkpoint slot | An optional location scoped to a task run, not an attempt, into which a unit may write resumable state that the next attempt receives (D31). |
| Fusion policy | The replaceable rule that chooses among legal groupings of nodes into units; its version is recorded on every plan (D33). |
| Pushdown | Running a relational node inside the warehouse that holds its inputs, instead of extracting the data. |
| Extraction cap | A configurable limit on data extracted from a warehouse; exceeding it stops the plan and asks the author. |
| Single-node guideline | A threshold beyond which work is flagged as exceeding in-process capacity. Made concrete in v0.10 as the planner's capacity check (D34). |
| Memory class | A node type's declared memory behaviour: streaming, blocking and spilling, or blocking and non-spilling (D34). |
| Repartition step | A unit that rewrites data hash-bucketed by a key, so that a node can fan out by a key other than the input's partitioning. |
| Conformance matrix | Built-in relational nodes × engines (DuckDB, Postgres, Snowflake); each cell is a fixture suite checking that the node gives the same answer on that engine. |
| Connection policy | Settings on a warehouse connection, set by the warehouse's owner: whether the platform may compute there, which compute cluster it uses, and an optional credit budget. |
| Plan pinning | Freezing a production workflow's placement so that changes are reported rather than applied. |
| Bring-your-own-compute (BYOC) | The deployment model in which execution runs on customer infrastructure and the vendor coordinates. |

## 3. Key reasoning and rejected alternatives

These explain why decisions went the way they did, so that they are not reopened unknowingly. Like the decisions themselves, they may be revisited.

1. **Bit-identical reproducibility was rejected** (D7). It is unattainable with floating point, parallelism and library changes, and users care about the same *result*. Tolerance-based comparators and explained verdicts are the valuable product; byte hashes remain internal accelerators.
2. **The comparator is explainability, not caching.** Caching trusts keys. Comparators explain why two runs differ; the churn example pinned a missing `random_state` as the first divergence in trace order.
3. **Containers rather than a single process like n8n** (D11). Conflicting dependencies (R, Python, bioinformatics binaries), isolation of untrusted code, resource control, HPC and Kubernetes portability, and pinned images all require containers. A container-free mode would mean two execution paths, an embedded metadata store and extra OS support.
4. **Hybrid cache key** (D8). Input-addressed keys give a plan before the run; content-addressed keys give early cutoff. Canonical hashing costs a re-read, hence the 1 GB default threshold; byte digests are free because they are streamed during the write.
5. **Identity-addressed rather than content-addressed storage** (D23). A content-addressed path needs the hash before the final location is known, forcing a second write of large outputs.
6. **Fixed dataset names** (D19). Simpler than renames with aliases; the immutable ID keeps future renames possible without migration.
7. **Uploads are ordinary managed datasets** (D4). No special path is needed; the engine rules treat them as file data.
8. **Engine selection is by location, not size** (D25). Moving data costs more than computing where it sits. Size only affects the extraction cap and the capacity check; once an engine shares a location with the in-process engines, such as Spark, capacity chooses between them (D34).
9. **One definition per built-in node** (D25, D27). A design with an in-process implementation plus optional SQL lowerings was rejected because it meant two implementations for some nodes. Built-in nodes are now Ibis expressions, with Polars implementations only by justified exception (D27, amended in v0.10).
10. **Tenant = the whole organisation** (D9). Projects are the permission scope and cache boundary. Cross-tenant cache sharing is never allowed, because a cache hit leaks the fact that a computation happened and its result.
11. **Four deployment topologies** (D22). Customer storage addresses integration and lock-in; hybrid addresses sovereignty; self-hosting suits open-source and air-gapped users. Bring-your-own-compute is now the primary model.
12. **Placement constraints deferred, with three seams kept** (D26). Constraints can be added later as additive changes, but the location of past attempts and artifacts cannot be reconstructed, so it is recorded from the first release. Cache hits pass through an eligibility filter, and the planner decides every placement explicitly. Ideas discussed but not decided are recorded in D26 under "Considered".
13. **Snowflake as the single second warehouse for v1** (D25). One warehouse rather than two, because each adds a conformance column, a paid CI account and an adapter. Snowflake over BigQuery because it runs on all three major clouds (which matters for hybrid customers), offers longer time travel on enterprise editions (supporting replay under D4), and is what data-engineering buyers most often run. BigQuery was recognised as the technically easier adapter.
14. **Ibis adopted, DuckDB kept** (D27). Ibis is a dataframe API that compiles to engines, not an engine. Replacing DuckDB with Ibis's Polars backend was rejected because it loses DuckDB's spilling of large joins and aggregations to disk. Ibis moves operations such as fill-forward and pivots from "Polars, never pushed down" to "pushable", and gives Python authors a pushdown-capable code node in v1.
15. **Data moves only out of warehouses** (D25). Following Dataiku DSS: when inputs sit in different locations, each warehouse's share is reduced by pushdown and the results are processed in-process. Staging the smaller side into the warehouse was dropped: it required write access the owner may not grant, could copy governed data (such as classified uploads) outside the platform's control, and created temporary tables to track. The cost (a small upload joined with a large warehouse table) is mitigated by pushdown before extraction and by the plan suggesting a warehouse storage target.
16. **Pushdown is automatic, within an owner's policy** (D28). Making pushdown opt-in would make "extract everything" the default, which is slower, costlier and worse for governance. But pushdown spends the customer's warehouse resources, so the warehouse owner, not the workflow author, sets the connection policy.
17. **No platform-run Spark in v1.** Spark as the only engine was rejected: it is slower on data that fits one machine, adds start-up latency to interactive use, makes the single-machine install heavier, nests a second scheduler inside units, and handles the Polars group poorly. Spark as an added engine was deferred: warehouse data is already covered by pushdown, genomics uses container fan-out, and lake-scale customers usually run their own Spark. Ibis's PySpark backend makes adding it later cheap.
18. **Repartition step instead of a distributed engine** (D25). Most dataframe work is local to a partition or a key; a repartition step supplies the shuffle that Spark would otherwise provide. Work that no key can divide remains flagged.
19. **Conformance matrix.** Engines disagree on integer division, nulls, casts, timestamps, rounding, float aggregation and collation. Because the planner, not the user, chooses where a node runs, the same node must give the same answer on every engine; the matrix enforces this.
20. **Bring-your-own-compute** (D22). The plane separation (D21) already allowed it; making it primary aligns with Dataiku DSS and with regulated customers. It requires customers to provide container compute, not only a warehouse, and it shifts commercial value away from managed infrastructure (see Part III).
21. **A pull-based agent in every deployment** (D29). Having the control plane call the Docker or Kubernetes API directly in self-hosted installations was rejected: hybrid would then need a second execution path. With the agent everywhere, hybrid differs only in where the control plane runs. The cost is one extra component and one extra hop on a single machine.
22. **Isolation enforced from the first slice** (D30). A tenant identifier on every entity (D5) is not enough on its own; scoping retrofitted into an existing codebase is easy to miss somewhere, and a single unscoped path is a cross-tenant leak.
23. **Phase separate from outcome** (D31). A single status enum tends to assume that every execution ends in success or failure, which D12 Seam 1 forbids. With a separate outcome, a long-lived execution simply never reaches the ended phase.
24. **Nested workflows inlined** (D31). A separate child run was rejected because it would resolve its inputs at a different instant from its parent and break the snapshot isolation of D14.
25. **Quality-gate holds are bounded** (D31). Indefinite suspension was rejected because D14 protects the resolved inputs of a run in progress, so an unresolved hold would pin storage indefinitely. A continuation after the timeout that reused the run's resolved inputs was also rejected, because those inputs are no longer protected once the run ends; a late override instead releases the quarantined version and lets downstream datasets be rebuilt on current data through normal staleness handling.
26. **A unit is a container; the runtime belongs to the segment** (D32). D25 and its worked examples already placed several engines in one unit, which contradicted "one runtime, one process". Making the segment explicit resolves this and lets warehouse queries join later as one more segment kind.
27. **Fully automatic fusion from the start** (D33). Manual-first sequencing was rejected: with a canvas of fine-grained nodes, every built-in node would become its own unit, the costly case in the fusion example. Legality is deterministic and needs no measurements; only a cost-informed policy does, so the policy is replaceable. Using composites as the manual fusion control was rejected because composition is a canvas convenience, not an execution concept.
28. **Cache keys chained through nodes** (D8, amended in v0.10). Keys chained through units depend on how nodes happen to be grouped, and automatic fusion moves unit boundaries whenever the policy, a pinned boundary or a resource ceiling changes, which would cause misses without any change in computation. Keys of intermediates are computed at plan time and never stored, so fusion's savings in storage and I/O are kept.
29. **Ibis first for every built-in node** (D27, amended in v0.10). One engine for the palette means one memory manager, one spilling model, one in-process conformance column and default eligibility for pushdown. Builtin and vectorised UDFs let fuzzy matching and parsing stay in Ibis. Using Ibis's Polars backend instead was rejected: Polars does not document spilling of operator state, and its semantics are further from the SQL warehouses that conformance compares against.
30. **No declared maximum dataset size** (D34). A size limit on a dataset was rejected because capacity depends on the operation and on the unit's slice of the data, not on the dataset as a whole. Observed statistics, memory classes and backend ceilings give the planner what it needs, and the same check later chooses between engines at the same location.
31. **Ephemeral extraction** (D35). Requiring every unversionable source to be copied was rejected: not every team needs reproducibility, and copying terabytes into the customer's own storage is a cost the platform should not impose. Storage is an explicit choice and versioning a property of the source; an ephemeral read of a versioned source loses nothing, and an ephemeral read of an unversioned source keeps complete provenance and read positions, losing only re-execution, verification and caching.
32. **Data-engineering practice first** (D36). Reproducibility is the differentiator, but most organisations do not need it, and imposing its constraints would push them away. Whatever costs storage, compute or freedom of practice for its sake is opt-in.
33. **Cursors derived, not stored** (D37). A separate per-task state store was rejected: it is a second source of truth whose update is not atomic with the data, so a failure between the two loses or duplicates rows. Deriving the cursor from the position record committed with the data makes it advance if and only if the data commits.

## 4. Technology choices so far

| Area | Choice | Status |
|---|---|---|
| Control-plane store | Postgres | Chosen |
| Artifact store | Object storage, pluggable; customer storage targets supported (D4) | Chosen |
| Execution backends | Kubernetes; HPC/Slurm via outbound agents (images commonly run with Apptainer); cloud batch; single-machine container deployment. The first slice uses the single-machine deployment and Kubernetes, driven by a pull-based agent (D29) | Chosen |
| In-process engines | DuckDB through Ibis for every built-in node (spills to disk); Polars for code nodes and justified exceptions; exchanging Arrow | Chosen |
| Relational node definitions | Ibis, compiling through SQLGlot | Chosen subject to the D27 spike |
| Warehouses (v1) | Postgres and Snowflake | Chosen |
| Table formats | Iceberg and Delta, used as the commit mechanism underneath where applicable | Chosen |
| Later engines | Spark, Flink, Ray, all against customer-operated clusters | Deferred |
| Standards | OpenLineage (S21), EDAM format ontology (D18) | Candidates |
| Canvas | React Flow or Vue Flow | Undecided |
| Not yet chosen | Control-plane implementation language(s), API style, authentication and identity stack, observability stack, frontend framework, image builder and registry tooling | Undecided |

## 5. Maintaining the record

- **Record only what is confirmed.** A proposal enters the decision log only once agreed. Unconfirmed proposals are listed in Part III.
- **IDs are stable.** Decisions (D), open items (S) and capability lines (CORE, DE, DS, MLE) keep their IDs; retired IDs are not reused. CORE 3.8 is currently unused.
- **Statuses.** Decided; Partly decided (direction confirmed, details open); Open. Resolved open items point to the decision that resolved them.
- **Revisions.** Each catalogue revision marks new lines with "new in v0.x" and records a summary in the masthead. Amended decisions say what changed and in which revision.
- **Register.** The catalogue is written in a neutral, third-person register with British spelling.
- **Exports.** A PDF export from v0.5 exists and is out of date.

---

# Part II · Capability catalogue

The following is the catalogue at v0.10, converted from the illustrated version. Figures added before v0.10 are described as drawn; v0.10 changes are textual and the illustrated catalogue has not yet been updated to match.

## Catalogue masthead

What the platform must let a user do, stated as capabilities rather than components. Each line is stated so that it can be accepted, deferred or removed individually before any of it becomes architecture.

- **Platform:** web-based workflow orchestration, containerised execution
- **Out of scope:** deep learning / visual network design
- **Audience:** project team
- **Decisions:** 39 recorded · two partly decided
- **Open items:** 18 open · 6 resolved (S1–S24)
- **Issued:** 4 October 2026
- **This revision (v0.10):** sets the first development slice (D29); enforces tenant and project isolation from the start (D30); records the execution state model (D31); defines the execution unit as a container holding engine segments (D32); makes fusion fully automatic with a replaceable policy and separates it from composition (D33); makes Ibis on DuckDB the engine for every built-in node, with Polars by exception (D27); replaces declared size limits with a capacity check in the plan (D34); makes copying of external sources an explicit author choice, independent of whether the source is versioned (D35); puts standard data-engineering practice first and makes reproducibility opt-in (D36); derives incremental cursors from committed metadata (D37); meets point-in-time retrieval without changing the dataset model (D38); excludes online model serving (D39); hides unreadable entities by default (D30); amends D1, D4, D7, D8, D11, D13, D17, D22, D23, D25 and D27 accordingly
- **Previous revision (v0.9):** defers placement constraints while keeping three seams (D26); confirms Snowflake as the first-release warehouse, stops the planner moving data into warehouses and adds a repartition step (D25); adopts Ibis for relational nodes (D27); sets warehouse connection policy and plan pinning (D28); makes bring-your-own-compute the primary deployment model (D22); incorporates the Dataset Lifecycle note and worked engine examples; and brings older wording into line with recorded decisions

---

## System overview

A web-based platform for assembling, scheduling, executing and monitoring multi-stage data and computation pipelines, and for establishing what each run can be trusted to reproduce.

Pipelines are composed on a visual canvas and compiled to a custom intermediate representation, which is the definitive description of the work to be done. From that representation the platform schedules and executes containerised units of work across local machines, Kubernetes clusters, HPC schedulers and cloud batch services, records complete provenance for every run, and reuses prior results wherever inputs and code are unchanged.

The platform is **domain-agnostic by design**. A single substrate — scheduling, execution, datasets, artifacts, provenance and access control — serves data engineering, data science and machine learning engineering, with bioinformatics sequence analysis as a demonstration domain rather than a specialisation.

**Vision.** Large-scale analysis should be reproducible by construction rather than by individual discipline. A pipeline built on this platform is a portable, versioned and shareable asset; every run carries a complete provenance record and a verifiable statement of how closely its results can be reproduced. Visual authoring lowers the barrier for practitioners who are not infrastructure specialists, while text round-tripping, custom code nodes and explicit control over parallelism, resources and execution backends keep the platform acceptable to engineers.

- **Reproducibility as a product capability.** Pinned environments and provenance are the baseline. Each run is assigned a tier, established by re-execution and comparison rather than asserted.
- **One substrate, three disciplines.** Datasets are first-class objects, which unifies ETL outputs, feature tables and scientific data under one lineage and scheduling model.
- **Visual authoring, production orchestration.** A canvas over an engine with the semantics engineers expect: logical intervals, backfills, fan-out, retries, quotas and fair scheduling.
- **Open core.** The core is open source. Managed infrastructure, multi-tenancy, enterprise support and AI assistance are commercial.

**Intended users.** Analysts and researchers who need dependable pipelines without operating the underlying infrastructure; data and platform engineers who require lineage, backfills and governance; and teams that must share, review and re-run each other's work.

**Excluded from this revision.** Deep learning and visual neural-network design; a native streaming runtime (batch first, then micro-batch, per D6, with the architectural seams for later streaming support recorded in D12); container-free local execution (D11); and online model serving, delegated to external serving systems (D39, MLE 4.2). Exclusions are recorded so that they are revisited deliberately rather than by default.

---

## How to read the catalogue

- **Four sections, not three.** The three disciplines sit on top of a shared substrate — scheduling, execution, provenance, artifacts. That substrate is section **CORE**. A capability required by more than one discipline belongs in that section; otherwise it is implemented three times.
- **Two markers carry meaning.** `[shapes the core]` means the item imposes a requirement on the scheduler or domain model and is expensive to retrofit — these are the ones to settle first. `[cross-discipline]` means the same capability is demanded from more than one direction. `[deferred]` marks a line a decision has pushed out of the initial scope, and `[new in v0.x]` records the revision that added a line. Revision v0.10 adds no capability lines; it revises the notes of existing ones.
- **Decisions are referenced as D1–D39, open items as S1–S24.** The decision log records what has been settled and what remains open; the open items carry forward unresolved questions of behaviour at scale, of the data lifecycle and of authoring and execution. Catalog notes reference both where they affect a line.
- **Most items are wrapping, not inventing.** Nearly everything under DS and MLE exists in sklearn, Polars, Optuna, SHAP, MLflow. The product is the palette and the reproducibility guarantees around them, not reimplementations. Items requiring original implementation are identified in the notes.
- **IDs are stable.** Items are referenced by ID in review and correspondence — `DE 1.3`, `CORE 2.6` — so that this document remains the single reference.

---

## Key terms

Vocabulary the rest of the document depends on. Each core concept is given a definition, a diagram of the underlying mechanism and a worked example based on a customer-churn pipeline used as the running example throughout.

#### IR — *intermediate representation*

The platform's **canonical, machine-readable definition of a workflow**: its nodes, their typed inputs and outputs, the edges and control-flow constructs between them, parameters, resource requests, pinned image digests, and retry, caching and side-effect declarations. The term comes from compilers, where the IR sits between the language people write and the code machines run.

The IR is **the single source of truth**. The canvas, the git-committed text form and imported templates are all views of it; backend submissions are all generated from it. Validation, cache keys, provenance records, version diffs and reproducibility checks all operate on the IR — never on canvas state or on a backend's own format. It is custom to this platform (D3) and carries its own schema version.

> *Diagram:* Authored in: Visual canvas, YAML / Python in git, Template import → **IR** (validated · versioned · hashed) → Compiled to: Kubernetes, HPC (Slurm), Local containers, Export: Argo / Airflow

**Semantic fields — what the node computes**

- Node type and implementation version, code, image digest
- Resolved parameters and declared environment
- Inputs, outputs, edges, control-flow constructs
- Declared randomness and external side effects

**Operational fields — how and where it runs**

- CPU, memory, GPU, timeout, retry policy
- Backend and queue selection
- Labels, descriptions, log level
- Canvas layout, kept as metadata beside the IR, not in it

Only semantic fields feed cache keys and reproducibility checks (D8), so changing memory or moving a node on the canvas never invalidates a result.

### Workflow structure

#### Node — *what the user draws*

One operation on the canvas, with typed inputs, typed outputs and parameters — what a user would call a **step**. Nodes describe *what* should happen; they say nothing about how the work is packaged for execution. Granularity is chosen by context (D1).

- **Fine-grained.** One small operation: a scaler, a join, drop nulls.
- **Coarse.** A large unit of work: a script, a SQL query, a tool such as BWA-MEM.
- **Composite.** A subworkflow collapsed into one node for readability and reuse.
- **Control-flow.** `if`, `map`, `loop`. Compute nothing; decide what runs next.

**Composition** is the user action that creates a composite node. It shapes the canvas only: at compile time a composite is flattened back into its inner nodes, and execution is planned from the flattened graph. Composition never implies fusion: a composite may become one execution unit, several, or part of a unit shared with nodes outside it (D33).

> *Diagram: A composite node on the canvas is flattened into its inner nodes at compile time; control-flow and other nodes pass through unchanged.*
>
> The composite **prep** node exists only on the canvas. At compile time it dissolves into **clean → impute → encode**; execution units are then formed from the flattened graph. The **map** is a control-flow node: it computes nothing itself, it instructs the orchestrator to run **train** 200 times.

> **Example.** The churn pipeline shows four nodes on the canvas: **extract** (a SQL query), **prep** (a composite the user collapsed), a **map** over 200 hyperparameter sets wrapping **train**, and **evaluate**. Clean, impute and encode are not visible on the canvas unless the composite is opened; the compiler always resolves them.

#### Execution unit — *what the orchestrator dispatches*

The smallest thing the orchestrator **schedules, retries, caches and records provenance for**. One or more nodes compiled into a single job that reads its inputs from storage, runs its nodes in one container, writes its outputs to storage and exits. Inside the unit, nodes are grouped into **engine segments** — consecutive nodes on one engine, such as a DuckDB query, a Polars lazy plan or a Python block — which hand data to each other in memory as Arrow (D32).

- **One container, one image.** The runtime belongs to each segment, not to the unit.
- **One resource request.** CPU, memory and GPU on one backend.
- **Stored in, stored out.** Intermediates between its nodes stay in memory.
- **Atomic.** Succeeds or fails as a whole; safe to re-run.

> *Diagram: The churn pipeline's eleven nodes compile into five execution units; outputs are stored only between units.*
>
> Eleven nodes, five execution units. Inside a unit, data passes between nodes in memory; outputs are written to storage only at the boundaries between units. **U5** stands alone because it writes to an external system.

At run time, one compiled unit can execute many times. Each execution is a **task run**; each try at a task run is an **attempt**. The record of every task run and attempt that actually happened is the **run trace** — always acyclic, because loop iterations are unrolled into separate task runs (D2).

> *Diagram: One execution unit becomes many task runs under a map, and each task run can have several attempts.*
>
> One compiled unit, many executions. A **map** turns U3 into 200 task runs. When task run 17's machine is lost, its lease expires and a **retry** creates attempt 2 of the same task run.

> **Example.** Change `max_depth` on train: U1 and U2 are reused from cache; U3, U4 and U5 rerun. Change a parameter on impute: all of U2 reruns, because impute shares a unit with its neighbours — cheap here, and if impute became expensive the user could pin a cache boundary after it and U2 would split in two.

#### Fusion — *grouping nodes into one unit*

Grouping adjacent nodes into one execution unit so they run in one container and never store what passes between them. It exists because every unit pays fixed overheads — starting a container, writing its output, the next unit reading it back, storing the intermediate, a scheduler round-trip — and for cheap operations those overheads dwarf the work itself. **Fusion is what makes fine-grained nodes affordable.** It is applied automatically by the planner; users can only split, by pinning a cache boundary or marking a node to run as its own unit (D33).

> *Diagram: Unfused, four nodes pay four container starts and three write-read round trips; fused, one start and data stays in memory.*
>
> The same four nodes, with and without fusion. ▶ marks a container start. Unfused, every edge is a write to storage and a read back; fused, the edges disappear into memory and only the final output is stored.

> **Example · indicative figures.** A 20-node preparation chain on a 2 GB table, each node doing about half a second of real work. Unfused: 20 × (≈10 s start-up + ≈20 s write + ≈20 s read) ≈ **17 minutes** and 40 GB of intermediates for 10 seconds of computation. Fused: one start-up, one read, one write — **under a minute**.

**Nodes can be fused only when**

- They share an image and execution location (D32)
- Their resource needs are compatible
- No control flow sits between them
- No output between them must be stored: a published dataset, an output used by several units, a pinned cache boundary, a read from a copied external source (D35)
- Neither has an external side effect
- Neither is marked to run as its own unit (D33)
- Grouping would not create a cycle between units

**What fused nodes give up, and how it is recovered**

- Per-node caching and retries: a change or failure reruns the whole unit
- Full intermediates: replaced by per-node statistics, traced row samples and fitted parameters
- Any intermediate can be regenerated on demand from the unit's stored inputs
- Development runs on samples execute unfused, retaining every intermediate (CORE 6.6)

### Caching

#### Caching — *task-output memoisation*

Before running an execution unit, the platform computes a **cache key** from everything that determines the unit's output. If an artifact already exists under that key and is still retained, the unit is skipped and the artifact reused. It applies to pipeline iteration, resumption after failure, sweeps with a shared prefix, shared templates and backfills. Verification runs and side-effecting nodes never use it.

> *Diagram: Changing node B changes its key, which changes the keys of C and F; A and E keep their keys and are reused.*
>
> Keys travel along the edges. Editing **B** changes key(B), which is part of key(C), which is part of key(F), so all three rerun. **A** and **E** never involved B, so their keys, and their cached outputs, are unchanged. All of this is known before the run starts.

- **Cache key.** A hash of a node's semantic IR fields — code, image digest, node version, resolved parameters, declared environment — plus the keys of the nodes feeding it, so the key of a stored output depends only on the subgraph that produces it, not on how nodes are grouped into units (D8). Keys of intermediates inside a unit are computed but never stored or looked up. Operational fields such as resources, backend, labels and canvas layout are excluded, so changing memory or moving a node never invalidates a result.
- **Input-addressed.** Input identity is the upstream *key*. Stable, cheap, and the full plan is known before the run starts — as in the diagram above.
- **Content-addressed.** Input identity is a hash of the upstream *output*. Allows early cutoff, but needs stable output hashing and decides the plan as the run proceeds. Used together with input-addressed keys (D8).
- **Canonicaliser.** Normalises an output — sorts rows, strips file metadata — so it can be hashed exactly for content addressing. No tolerance; distinct from a comparator.

> *Diagram: A harmless edit to B reruns everything downstream under input-addressed keys, but only B under content-addressed keys.*
>
> The difference between the two strategies. Editing a comment in **B** changes nothing it produces. Input-addressed keys cannot detect this, so C and D rerun. Content-addressed keys hash B's new output, find it unchanged, and reuse C and D — **early cutoff** — at the price of hashing outputs and not knowing the plan in advance.

**The platform uses both (D8).** Input-addressed keys are computed for every node, chained through the nodes that feed it, so the whole plan is known before the run starts. In addition, artifacts small enough to hash cheaply get a canonical content hash recorded when they are written; nodes whose stored inputs all carry one also get a content key. A unit is skipped if every one of its stored outputs is found under either key.

> *Diagram: A unit is checked against its input-addressed key first, then against its content key, and only runs if both miss.*
>
> The hybrid lookup for one unit. The content key exists only where the upstream outputs were small enough to hash when they were written — the unit being skipped is never run to produce a hash of its own.

**A lookup is not a check.** Finding a key means "this exact recipe on these exact inputs has been computed before", so the stored output is reused without re-running anything. Caching *trusts* that a unit is a function of its key; confirming that a rerun really produces matching outputs is the job of verification runs and comparators, which deliberately bypass the cache.

**False hit · a correctness bug**

- The key missed something that affects the output, so a stale result is served silently
- Causes: undeclared inputs, mutable tags, code outside the image, unseeded replicates collapsing into one, side effects skipped, a bug fix in a built-in node

**False miss · a cost bug**

- The key included something irrelevant, so work is repeated needlessly
- Causes: operational fields in the key, non-canonical parameters, byte-unstable outputs, harmless upstream edits, image rebuilds

> **Example · undeclared external input.** The extract node runs `SELECT * FROM customers`. The query text never changes, so neither does its key; without a governing rule the platform would continue to serve the previously cached result indefinitely. The rule: a node reading an external source is not cacheable unless its key includes a version of that source (an Iceberg snapshot, an S3 object version, or the logical interval if data per interval is immutable). Where correct behaviour is uncertain, the design prefers a miss.

### Reproducibility

#### Reproducibility — *a verified, per-run claim*

The platform's ability to re-execute a recorded run and state precisely **how closely the new outputs match the originals, and why** — not a yes/no badge. The goal is the same result, not byte-identical files (D7). A tier belongs to a *run*, not a workflow: fixing a workflow makes future runs more reproducible, never past ones. Tiers are as recorded in D7.

| Tier | Guarantee | Requires | What caps a run here |
|---|---|---|---|
| Traceable | A complete record of what ran and on what. Auditable; re-execution not assured. | Complete provenance record | Live external inputs with no snapshot; deleted images; inputs removed by retention |
| Re-executable | A rerun executes the same code on the same inputs in the same environment. Outputs may differ. | Image digests pinned, every input retained or snapshotted, parameters and environment recorded | Unseeded randomness, clock reads, network calls inside a task |
| Reproducible | A rerun produces the same outputs, as judged by comparators within recorded tolerances. | Re-executable, plus a passing verification run | — |

> *Diagram: A run climbs from Traceable to Re-executable by pinning inputs, to Reproducible by passing verification, and falls back to Traceable when its inputs are deleted.*
>
> How a run moves between tiers. Solid arrows raise a run's tier; dashed arrows are **decay**: once a run's inputs are garbage-collected it can no longer be re-executed, whatever tier it had reached.

The workflow definition can prove a **ceiling** — network access caps a run at Re-executable — but only a verification run can establish Reproducible. Custom code nodes default to Re-executable until verified. A run's tier is set by the weakest node on each path.

- **Verification run.** A deliberate re-execution of a recorded run that bypasses the cache and replays recorded inputs rather than re-fetching them, then compares every output with the original.
- **Comparator.** Judges whether two versions of an output are the same result and explains the verdict: tables ignoring row order with float tolerance, models by predictions on a probe dataset, metrics within a tolerance, figures by their underlying data. Returns a status, the tolerance used, the maximum deviation and a diff report. Outputs with no comparator can only be compared byte for byte.

> *Diagram: A verification run compares every output; the first node whose output differs is the cause, and differences after it are consequences.*
>
> Verifying run #4127. Comparators check every output in trace order. **train_model** is the first divergence; evaluate and the final outputs differ only because their inputs did. Verdict: **Re-executable (verified)**, blocked from Reproducible by train_model.

> **Example.** Run #4127 is verified before its model goes for approval. The report pins the cause to one missing `random_state`; AUC moved from 0.8472 to 0.8491. The user fixes it and runs again as #4203, which verifies as **Reproducible**. #4127 stays Re-executable forever — its random draws were never recorded — so the approval should cite #4203.

### Data

- **Artifact.** Any stored output of an execution unit, often temporary, stored at an identity-addressed path and described by a manifest in the catalogue (D23).
- **Dataset.** A named, versioned, long-lived data asset with an owner and consumers, independent of the run that wrote it (D4). Every dataset version is an artifact or, for an external dataset, a reference; most artifacts never become dataset versions.
- **Logical interval.** The slice of time a run is *for* (e.g. 2026-09-19), as opposed to when it happened to execute. Makes reruns and backfills deterministic.

---

## Architecture planes

The platform is divided into four planes by responsibility and trust. Storage systems belong to planes rather than forming planes of their own. The division is recorded in D21; the deployment topologies it makes possible are recorded in D22.

> *Diagram: The four planes stacked: interface, control, data and observability, with the traffic that crosses between them.*
>
> **The four planes.** Each plane has one responsibility and one trust level. Bulk data stays in the data plane; the control plane holds only metadata and never runs user or plugin code; observability receives append-only telemetry and is never needed for correctness.

- **Interface.** Web application, API, CLI and git synchronisation. Authenticates people, turns their actions into definition changes or commands, and presents state. Holds no state of its own; scales with users.
- **Control.** Compiler, scheduler, reconciler, dispatcher, catalog, cache index, provenance, policy and plugin registry. The single source of truth for what exists and what has happened, held in Postgres. Scales with tasks, partitions and datasets, not data volume.
- **Data.** Execution units in containers on a backend. The unit runtime resolves inputs, runs fused nodes, calls format plugins, stages outputs and requests commits. Holds no state beyond a unit's life; scales with data and compute; sandboxed.
- **Observability.** Live log tail, log archive, metrics time series, node events and alerts. High-volume and append-only, stored outside the metadata database; redacts secrets on ingestion.

### Invariants

- **Bulk data.** Never passes through the interface or control planes. They handle pointers, statistics and pre-computed previews only.
- **Untrusted code.** Runs only in the data plane. The control plane executes platform code exclusively.
- **Disposability.** Any data-plane component can be terminated at any moment. Leases expire, units are retried, and fencing prevents a superseded attempt from committing.
- **Correctness.** Never depends on observability. Telemetry may be delayed or lost; state may not.

> *Diagram: One run crossing the planes: the interface starts it, the control plane plans and leases it, the data plane executes it while streaming telemetry, and the control plane commits the result.*
>
> **One run across the planes.** The control plane plans and leases work; the data plane executes and asks to commit; only the control plane can make a result current. Telemetry flows sideways into observability and never back into decisions.

### Failure independence

| Outage | Effect |
|---|---|
| Control plane | Running units continue and buffer their commit requests until it returns. No new work is dispatched and no result becomes current. |
| Data-plane node | Its leases expire and affected units are retried elsewhere. Fencing rejects any late commit from the lost attempts. |
| Observability | Runs continue unaffected. Logs and metrics are buffered or partially lost; no decision depends on them. |
| Interface | Scheduled work continues; people cannot start, change or inspect work until it returns. |

### Storage by plane

| Storage | Plane | Holds |
|---|---|---|
| Postgres | Control | Definitions, runs, datasets, versions, cache index, provenance |
| Object storage (artifact store) | Data | Platform-owned bytes; the control plane holds only pointers |
| Warehouses, lakehouses, user buckets | Data (external) | Referenced data the platform does not own |
| Log archive, time-series store | Observability | Logs, metrics and events |
| Git repositories | Interface | Workflow definitions as text |

> *Diagram: Four deployment options ordered by how much the customer controls: self-hosted, fully managed, managed with customer storage, and hybrid.*
>
> **Deployment topologies.** Because the control plane never handles bulk data, the planes can run in different places. Customers trade convenience for control: from fully managed, through managed compute writing to their own storage, to hybrid, where execution agents in their environment connect outward and their data never leaves it, and finally self-hosting, where they operate everything.

| Option | Operations | Compute | Storage | Typical customer |
|---|---|---|---|---|
| Fully managed | Vendor | Vendor | Vendor | Small teams, research groups, trials |
| Managed, customer storage | Vendor | Vendor | Customer | Integration with an existing lakehouse; no lock-in |
| Hybrid | Vendor | Customer | Customer | Regulated and sovereignty-sensitive organisations |
| Self-hosted | Customer | Customer | Customer | Open-source users, air-gapped environments |

> **Why hybrid matters.** An enterprise can adopt the hosted product without moving data out of its own cloud account or HPC cluster. Execution agents inside the customer's environment pull work from the hosted control plane over outbound connections, mint storage credentials locally, and return only metadata and events. This is a strong argument for regulated and data-sovereign customers, and it exists only because the control plane never touches bulk data.

---

## Processing engines in practice `[new in v0.9]`

Two worked examples showing how the planner applies D25 to D28 under the bring-your-own-compute model (D22): where each unit runs, what data moves, and why. Figures are indicative.

### Retail · warehouse and file data

A retailer keeps orders and customers in Snowflake, web events as Parquet in its own bucket, and a small store-to-region mapping uploaded through the browser. One workflow builds a daily sales table, a customer-activity feature table and a model.

| Dataset | Location | Size | Role |
|---|---|---|---|
| `raw.orders` | Snowflake | about 12 GB per daily partition | input |
| `raw.customers` | Snowflake | about 2 GB, 14 columns | input |
| `ref.store_regions` | Object storage (upload) | 3 MB | input |
| `raw.web_events` | Object storage (Parquet) | about 40 GB per daily partition | input |
| `curated.daily_sales` | Storage target: Snowflake | small | output |
| `features.customer_activity` | Storage target: object storage | small | output, read by training |

> *Diagram: Retail plan: Snowflake reduces orders and customers by pushdown and the reduced results are extracted into execution units on customer compute; the uploaded mapping and the web events are read from object storage; daily sales is published back to Snowflake and the feature table to object storage, from which training reads.*
>
> **Retail plan.** Each warehouse's share of the work is reduced by pushdown and only the result is extracted into units on customer compute. The uploaded mapping is never copied into Snowflake: the join that needs it runs in-process. **curated.daily_sales** is written to Snowflake only because Snowflake is its storage target.

| Unit | Engine and location | Reason |
|---|---|---|
| U1 | Snowflake query, then Ibis on DuckDB | The filter and the customer join are pushed down because both inputs are in Snowflake. The join with `ref.store_regions` spans locations, so the reduced result is extracted and joined in-process. The plan suggests storing `ref.store_regions` in Snowflake, which would let U1 run as one pushed-down query. |
| U2 | Snowflake query, then Ibis on DuckDB | Only 3 of 14 customer columns are extracted after pushdown. Sessionisation by inactivity gap is expressible with window functions, so under Ibis first (D27) it chains with the join and aggregation into one DuckDB segment. Before v0.10 it was assigned to Polars as sequential logic. |
| U3 | Python | A training code node, reading the published feature table. |

| Variation | Effect on the plan |
|---|---|
| A · mapping stored in Snowflake | The owner gives `ref.store_regions` Snowflake as its storage target. U1 becomes a single pushed-down query, nothing is extracted, and the result is written inside Snowflake. |
| B · extraction over the cap | If the reduced orders data exceeds the configured extraction cap, the plan stops and asks the author instead of proceeding, and repeats the suggestion of variation A (D25). |
| C · 2 TB of events per day | The partition fails the planner's capacity check (D34). Sessionisation groups by customer while the data is partitioned by day, so the planner inserts a repartition step: about 256 buckets of 8 GB by customer, with U2 fanned out per bucket and the extracted customer columns read by every bucket (CORE 2.26). |

A variation in which `raw.customers` may not leave Snowflake applies only once placement constraints are introduced (D26).

### Genomics · non-tabular data

A research group aligns and calls variants for 40 sequencing samples on its own HPC cluster, then joins the results with a small clinical spreadsheet and produces a report. Nothing in the flow touches a warehouse.

> *Diagram: Genomics flow: FASTQ files are read in place and aligned, variant-called and converted by containers on the customer's HPC cluster, fanned out by sample and by genomic region; the Parquet results are joined with an uploaded clinical file on DuckDB and reported in Python on the customer's Kubernetes cluster.*
>
> **Genomics plan.** One workflow, three runtimes (container commands, Ibis on DuckDB, Python) and three ways of parallelising: by item (40 samples), by split within an item (24 regions read through the BAM index), and a single unit for the join and report. Each unit's backend is chosen separately, all of it on customer infrastructure.

| Step | Runtime and backend | Parallelism and reason |
|---|---|---|
| Align | BWA container command, HPC agent | Fan-out by item: one unit per sample. The FASTQ files are registered in place rather than uploaded (D4). |
| Call variants | GATK container command, HPC agent | Fan-out by split: the genomics family plugin reports splits through the BAM index, giving 24 regions per sample (CORE 6.19). BAM and index travel together as one file group (CORE 6.16). |
| Convert | bcftools container command, HPC agent | Fan-out by item, producing Parquet so that the next step can treat the variants as tabular data. |
| Join | Ibis on DuckDB, Kubernetes | Both inputs are files on object storage, so the join runs in-process (D25, D27). |
| Report | Python, Kubernetes | A single unit producing the summary report. |

---

## Dataset lifecycle `[new in v0.9]`

What it means in practice for datasets to be first-class objects rather than the outputs of runs: the properties a dataset carries, how versions are published, how state is tracked per partition, and what becomes possible once the platform reasons about data rather than about pipeline invocations. The section elaborates D4 and the data-lifecycle decisions D13 to D16, D19, D20 and D24. Figures are numbered within the section.

### 1 · What a dataset carries

A dataset is an aggregate with its own identity and lifecycle. The distinction from an artifact is the whole point: an **artifact** is a run-scoped output, often temporary; a **dataset version** is a published asset with an owner, a contract and consumers. Every dataset version is an artifact or a reference; most artifacts never become dataset versions.

> *Diagram: A dataset object with identity, schema, policy and state on the left, its ordered versions in the centre, and each version's materialisation on the right.*
>
> **Figure 1.** **Anatomy.** The dataset carries identity, schema and policy that outlive any run. Each version is one materialisation, and a version is either **managed** (bytes in the platform's artifact store) or **external** (a reference to data the platform does not own). Both are the same kind of object; only the pointer differs.

- **Identity.** A stable name, owner, description and tags that survive the deletion of any pipeline that writes to it.
- **Schema and contract.** Columns, types and keys, with an evolution rule enforced at publication. Producers are validated; consumers are guaranteed compatibility.
- **Versions.** An ordered sequence of materialisations. Each records its producing run, the input positions consumed, its statistics and its state.
- **Partitions.** Addressable subdivisions of a version, each with independent state, lineage and rerun.
- **Materialisation policy.** Managed (bytes in the platform's artifact store) or external (a reference to a warehouse table or bucket the platform does not own).
- **Declared reads and writes.** Nodes declare the datasets they consume and produce; lineage and permissions follow from those declarations.
- **Freshness expectation.** A stated currency requirement, which makes staleness measurable independently of whether a schedule ran.
- **Classification and retention.** Data classification, retention period and erasure obligations, propagated to derived datasets along lineage.
- **Consumers.** The set of pipelines, datasets and models that read it — the basis for impact analysis before a change or deletion.

### 2 · Publication

Publication is the moment an artifact becomes part of a dataset's history. It is also the enforcement point for the contract, which is what allows a consumer to depend on a dataset rather than on the pipeline that happens to write it. The binding is declared once — a node's output is bound to a named dataset — and every subsequent run of that node publishes automatically; publication is not a manual step performed per run.

- **Declared binding.** The normal case. An output port is bound to a dataset in the node configuration and in the text definition. Each run publishes a new version of the partitions it wrote.
- **Gated publication.** For sensitive or heavily consumed datasets, a version becomes current only after a passing quality gate or an approval, using the same externally resumed execution state as an approval step.
- **Manual promotion.** An artifact from an exploratory run is promoted into a dataset after the fact, which is how a useful one-off becomes a maintained asset.
- **Unbound outputs.** Everything else remains a run-scoped artifact: subject to retention, absent from the catalog, and never a dependency for another pipeline.

> *Diagram: A task run produces an artifact, which is validated against the dataset's contract and either becomes a new version or is refused.*
>
> **Figure 2.** **Publication.** An artifact is a run-scoped output; a dataset version is a published asset. Publication validates the artifact against the dataset's schema contract, assigns the next version, records lineage and notifies consumers. A breaking change fails the producer rather than corrupting the consumer.

### 3 · Versions and partitions

State lives at the partition level. This is what separates a dataset model from a folder of files, and it is what makes backfills, partial reruns and incremental caching expressible. Partitions and versions are independent axes and are easily confused: a partition is *which slice* of the data, a version is *state over time*. Partitions are not sub-versions, and versions are not created only by structural change — a routine daily run that adds one day of data produces a new version with an unchanged schema.

> *Diagram: A grid of dataset partitions by date, each marked available, stale, not yet materialised or failed, with staleness propagating downstream.*
>
> **Figure 3.** **Partitions.** State is tracked per partition, not per dataset. A change to one upstream partition marks exactly the downstream partitions that depend on it, which is what makes partition-level rerun and backfill possible without recomputing history.

> *Diagram: A grid with partitions across and snapshots down, showing that each publication creates a snapshot which reuses unchanged partition versions and points at newly written ones.*
>
> **Figure 4.** **Two axes.** A **partition** is a slice of the key space, fixed by the partitioning scheme. A **version** is state over time. Every successful publication creates a new snapshot, whether or not anything structural changed; the snapshot reuses the partition versions it did not touch. Schema evolution is a third, separate property recorded on the version.

> *Diagram: States of a dataset version: declared, materialising, available, superseded, expired, with a quarantined branch when a quality gate fails.*
>
> **Figure 5.** **Version states.** Versions are immutable once available; a correction produces a new version rather than editing an old one. Superseded versions stay readable so that historical runs remain re-executable until retention removes them — the point at which affected runs decay to Traceable. A quarantined version may later be released by an override (D31).

### 4 · Contract and expectation

Both the schema contract and the freshness expectation are declared by the dataset owner, with inference used to avoid imposing ceremony on exploratory work.

- **Observed schema.** Default for a new dataset. The schema is inferred at first publication and recorded; changes are logged but not enforced.
- **Enforced contract.** Promoted by the owner, normally when another pipeline begins consuming the dataset. The owner selects an evolution rule — additive only, widening permitted, or breaking changes requiring a major version — and publications are validated against it.
- **Freshness expectation.** An optional declared target and maximum lateness. Where none is declared, a default is derived from the production schedule. Breaches raise alerts and mark the dataset stale in the catalog, independently of whether a scheduled run occurred.
- **Where it is defined.** In the interface and in the text definition, since dataset declarations round-trip to version control with the rest of the pipeline definition.

### 5 · Lineage

Because reads and writes are declared, the lineage graph is derived rather than maintained by hand, and it records position ranges rather than only identities.

> *Diagram: Lineage alternating between datasets and runs, with reads and writes labelled, and a second row showing column-level lineage limited to declarative nodes.*
>
> **Figure 6.** **Lineage.** Because nodes declare what they read and write, lineage is derived rather than documented. Reads record the range of positions consumed, so the graph answers both “what produced this” and “what must change if this changes”. Column-level detail is available where transformation logic can be parsed.

### 6 · Reconciliation

The behavioural consequence of the model: the platform can be asked for a state of the data rather than for the execution of a pipeline.

> *Diagram: A request for a dataset to be current is compared against observed partition state, producing a minimal plan that is dispatched and fed back into observed state.*
>
> **Figure 7.** **Asset-based scheduling.** Making datasets first-class allows a second entry point: instead of invoking a pipeline, a request states the data that should exist. The reconciler derives the minimum work required. Data-triggered scheduling, cross-workflow dependencies and partition-level rerun become the same mechanism.

### 7 · Governance

Classification, retention and erasure are properties of the asset, so they travel with it. **Classification** here means data sensitivity and handling, not statistical classification: a sensitivity level (public, internal, confidential, restricted) and any special categories that apply (PII, PHI, PCI, export-controlled). It drives masking, access control, retention, residency and erasure obligations.

- **Declared by the owner.** Optionally assisted by automated detection, which proposes candidate classifications for confirmation rather than applying them silently.
- **Inherited along lineage.** A derived dataset takes the highest sensitivity among its inputs by default.
- **Declassification is explicit.** Aggregation or anonymisation may genuinely reduce sensitivity, but only an auditable assertion by an accountable owner may lower a classification. It is never an automatic consequence of a transformation.

> *Diagram: An erasure request entering at the raw dataset and cascading through derived datasets to a model flagged for retraining.*
>
> **Figure 8.** **Governance.** A dataset's classification is a property of the asset, so it propagates to everything derived from it. An erasure obligation follows the same edges, which is only tractable because lineage is derived automatically.

### 8 · End-to-end walkthrough

One dataset, from declaration to deletion, with the figure that illustrates each stage.

1. **Declaration.** The dataset is registered before any data exists: name, owner, schema contract, classification, retention and freshness expectation. A pipeline may reference it as an output while it is still empty. *(Fig 1)*
2. **First materialisation.** A run produces an artifact. Publication validates it against the contract, assigns version 1 and records which input positions were consumed. *(Fig 2)*
3. **Incremental updates.** Subsequent runs add or replace partitions. Each publication produces a new snapshot that reuses untouched partition versions; the previous snapshot remains readable and is marked superseded. *(Fig 3, 4, 5)*
4. **Consumption.** Downstream nodes declare the dataset as an input. Lineage is derived from those declarations, and access is enforced against the dataset rather than a storage path. *(Fig 6)*
5. **Staleness.** A change to an upstream partition marks the dependent downstream partitions stale. Freshness is evaluated against the dataset's SLA, not against a schedule having run. *(Fig 3)*
6. **Reconciliation.** A request for the dataset to be current yields a minimal plan: only stale or missing partitions, and only the upstream work they require. *(Fig 7)*
7. **Schema change.** An additive change publishes normally. A breaking change is refused at publication and reported to the producer, leaving consumers on the last valid version. *(Fig 2)*
8. **Governance events.** Classification propagates to derived datasets. An erasure request cascades along the same lineage edges, rewriting, rebuilding and flagging as it goes. *(Fig 8)*
9. **Retention and decay.** Versions expire under the retention policy. Runs whose inputs have expired lose the ability to be re-executed and are reported as Traceable rather than silently unverifiable. *(Fig 5)*
10. **Deprecation.** The dataset is marked deprecated while consumers migrate, then deleted. Consumer lists make the blast radius explicit before deletion occurs.

The model shown here assumes D4 (datasets as first-class objects) and the seams recorded in D12. Asset-based reconciliation (Figure 7) is recorded in D24, within a single project in the first release.

---

## Decision log

Decisions taken, decisions taken in principle with details outstanding, and questions still open. A recommended position is recorded against each open item.

Status values: **Decided**: confirmed; **Partly decided**: direction confirmed, details open; **Open**: awaiting a decision.

#### D1 · Node granularity

**Status:** Decided

Granularity is chosen by context: fine-grained nodes where step-by-step control helps, coarse nodes where a whole script is the natural unit. Composition collapses large flows into a single node nested inside a workflow.

- **Follows.** Nodes and execution units are separate concepts; the canvas node is not the unit of dispatch.
- **Follows.** Fusion is applied automatically by the planner; users control it by splitting (D33).
- **Sequencing.** Node and execution unit are separate in the IR from the outset. Amended in v0.10 by D33: fusion is fully automatic from the first slice, behind a replaceable policy, and composites play no part in it. The previous sequencing — manual fusion first by marking a composite "run as one unit", automatic fusion later — is withdrawn. Users can pin a cache boundary inside a fused chain or mark a node to run as its own unit.

*References:* CORE 1.4 · DS section · DE 2

#### D2 · Graph model

**Status:** Decided

Workflows are control-flow graphs, not strictly DAGs. Conditionals, loops and adaptive iteration are supported.

- **Structured.** Only structured constructs are permitted — if/else, map, and bounded loops with a maximum iteration count — and no arbitrary back-edges, so definitions remain statically analysable.
- **Unrolled trace.** Each loop iteration unrolls into distinct task runs at execution, so the run trace is always acyclic and provenance and caching operate on it unchanged.

*References:* CORE 2.10 · DS 3.6 · MLE 5.5

#### D3 · IR and execution engines

**Status:** Decided

The IR is custom to the platform and compiles down to existing engines and backends. No external engine's model becomes the domain model.

- **Dispatch.** The platform's own orchestrator owns control flow and state and dispatches individual execution units to backends. Compiling a whole workflow into Argo or Airflow is offered as an export for workflows without loops, not as the execution path.
- **Follows.** The IR has a formal spec and schema version from day one, with migrations, because users commit it to git.

*References:* CORE 1.6 · CORE 2.9

#### D4 · Datasets as first-class objects

**Status:** Decided

Datasets are domain objects with their own identity, versions, partitions, schema and owner, independent of the runs that produce them.

- **Follows.** Dataset and artifact are distinct terms (see key terms).
- **Managed or external.** Decided by who owns the data's lifecycle, not by where the bytes sit. A **managed** dataset is written, versioned, committed and retained by the platform. An **external** dataset is written by someone else; the platform only references it.
- **External sources.** A versionable source — an Iceberg snapshot, an S3 object version — is referenced and its version recorded. An unversionable source is copied into a raw dataset at ingestion by default (DE 1.7). Its owner may instead declare **reference without copying**, accepting that runs reading it are capped at Traceable. Amended in v0.10 by D35: nothing is copied by default; for every external source the author chooses explicitly between an ephemeral read, which stores nothing and may be fused into downstream transformations, and a copy, while the source's version, where it has one, is recorded either way.
- **Storage targets.** A managed dataset may live on platform storage or on the customer's own: object storage in their account, a table registered in their lakehouse catalog, or a table in their warehouse. Targets are set at tenant, project or dataset level, each overriding the one above. Where a warehouse is the target, old versions remain replayable only within its time-travel retention.
- **Integrity.** The platform owns its prefix or schema within customer storage. Manifests carry checksums, so out-of-band modification is detected and the affected version flagged.
- **Retention.** Either delegated to the platform, which then deletes expired versions in customer storage, or left to the customer's own lifecycle rules, in which case the platform detects missing files and marks the version expired.
- **Delivery.** Separately, a sink node may deliver a copy of a dataset into a customer system. A delivered copy is an export, not the dataset: it is neither versioned nor protected by the platform.
- **Uploads.** A file uploaded through the browser, CLI or SDK becomes a managed dataset whose producer is the upload action rather than a workflow. From then on it is versioned, validated, classified, retained and consumed like any other dataset. A dataset is either upload-fed or workflow-fed, never both (D13).
- **Upload path.** Bytes go directly to the project's storage target through pre-signed, resumable multipart transfers and never pass through the interface or control planes (D21). Checksums are verified on arrival; each upload is a new version, and an identical re-upload is recognised by its digest and recorded as a no-op. The family plugin validates the file at publication, and the schema starts in observed mode (DE 5.8).
- **Originals.** The uploaded file is kept unchanged as the source of truth. Where it helps performance, an optimised copy such as Parquet is produced as a derived artifact, never as a replacement.
- **Intended use.** Uploads suit reference, sample and labelled data and models. Bulk data is connected or registered in place; very large files use the CLI or SDK with the same mechanism. The cloud edition caps the size of browser uploads.

*References:* CORE 6.1 · CORE 6.25 · DE 5 · MLE 1

#### D5 · Distribution and tenancy

**Status:** Decided

Open core. Core features are open source. Managed cloud infrastructure, multi-tenancy, enterprise support and AI integration are paid.

- **Deferred.** The licence, the precise line between open and paid features, and whether open-source users may supply their own AI provider keys are deferred. They do not shape the architecture in the early stages. Options and a recommended direction were discussed and remain on record for when the decision is taken.
- **Structural now.** Every entity carries a tenant identifier from the outset; the open-source edition runs as a single tenant, and the cloud edition is the same core plus extensions rather than a fork. Isolation is enforced along every access path from the first slice (D30).
- **Structural now.** Capabilities likely to be commercial — authentication providers, access-policy enforcement, audit sinks, AI providers — sit behind extension interfaces from the start, so the open/paid line can be drawn later without restructuring and commercial code can live in a separate module.
- **Timing.** The licence must be chosen before the first public release or before external contributions are accepted, whichever comes first; relicensing afterwards requires every contributor's consent. The repository is currently private (D29).
- **Direction.** SDKs, the IR specification and plugin interfaces are expected to be permissively licensed whatever is chosen for the core server, since plugin authors and integrators will not build on restrictive terms. Reproducibility features, the HPC backend and basic role-based access control are expected to remain open.

*References:* CORE 7

#### D6 · Streaming

**Status:** Decided

Batch only at first; micro-batch next (frequent scheduled runs over incremental data); managed long-running streaming jobs possibly later. A native streaming runtime is out of scope.

- **Follows.** Micro-batch needs no new execution model; it builds on incremental extraction state and logical intervals.
- **Follows.** The domain model leaves room for a long-lived "deployment" entity next to finite runs, without building it now. The seams that keep this option open are recorded in D12.

*References:* DE 2.8 · DE 2.9 · DE 1.2 · CORE 3.3

#### D7 · Reproducibility guarantee

**Status:** Decided

The goal is the same output, not byte-identical files. Bit-identical reproducibility is not a user-facing goal; byte hashes remain an internal tool for fast verification and storage deduplication.

- **Tiers.** **Traceable** — a complete record of what ran and on what; re-execution is not assured. **Re-executable** — same code, inputs and environment; outputs may differ. **Reproducible** — same outputs, confirmed by comparators within recorded tolerances.
- **Ceiling.** The definition can prove a ceiling statically — network access, for example, caps a run at Re-executable — but Reproducible is reached only through a passing verification run. Custom code nodes default to Re-executable until verified.
- **Weakest link.** A run's tier is set by the weakest node on each path.
- **Decay.** A run drops to Traceable when its inputs are garbage-collected; where the reproducibility setting is on, the interface warns before this happens (D36). Inputs of runs still in progress are protected (D14).
- **Per run.** A tier belongs to a run, not a workflow. Fixing a workflow makes future runs more reproducible, never past ones.

*References:* CORE 5.4 · CORE 5.7 · CORE 6.5

#### D8 · Cache keying

**Status:** Decided

Hybrid. Every node gets an **input-addressed** key, built from its own semantic fields plus the keys of the nodes feeding it, so the full plan of what will rerun is known before the run starts. Artifacts small enough to hash cheaply also get a canonical **content hash** when written; where every stored input a node depends on carries one, it gets a second, content-addressed key. Only outputs stored at unit boundaries are looked up and stored under their keys: a unit is skipped if every one of its stored outputs is found under either key, and on a miss its outputs are stored under both.

- **Node-level chaining.** Amended in v0.10: keys were previously chained through units, from each unit's semantic fields and the keys of its upstream units. Keys of intermediates inside a unit are now computed at plan time and discarded, never stored or looked up, so fusion's savings are unaffected, and the key of a stored output no longer changes when automatic fusion regroups nodes (D33).
- **Follows.** Early cutoff where it is cheap: an upstream unit that reran but produced identical output no longer forces expensive downstream work to repeat.
- **Follows.** A lookup is a lookup, not a check — caching trusts that a unit is a function of its key. Confirming that a rerun matches is the job of verification runs (CORE 5.7).
- **Byte digests.** A byte-level digest is computed for every file as it is written, at negligible cost because it is streamed alongside the write. No threshold applies.
- **Threshold.** Canonical content hashing — which may require re-reading and sorting — applies by default to artifacts up to **1 GB**. This is an initial default to be tuned from measurements during development, and configurable per project.
- **Overrides.** A node or dataset may opt in to canonical hashing above the threshold where downstream work is expensive enough to justify it, or opt out below it.

*References:* CORE 2.6 · CORE 2.12 · CORE 2.13 · CORE 5.8

#### D9 · Cache scope

**Status:** Decided

A tenant is the unit of hard isolation and billing — for an enterprise, the whole organisation. Within a tenant, work is organised into projects, which are the default permission scope; users and teams hold roles per project. Cached results are reused within a project by default, may be reused across projects of the same tenant by opt-in, and are never reused across tenants.

- **Hierarchy.** Tenant (organisation) → projects or workspaces → users and teams. Sharing datasets and workflows between members and teams is the normal case, governed by project permissions (S20). A self-hosted open-source installation is effectively a single tenant.
- **Permission check.** A project may reuse a cached output produced elsewhere in the tenant only if it could read every input that produced it and is cleared for the output's classification. A cache hit otherwise reveals that a computation took place and discloses its result.
- **Public data.** Outputs derived solely from explicitly public reference data, such as a published reference genome index, may be shared more widely.
- **Later.** Hard isolation boundaries inside a tenant — for a regulated division, subsidiary or separate legal entity — are not required in the first release, but the model must not preclude them.

*References:* CORE 2.6 · CORE 7.6

#### D10 · Where column-level lineage stops

**Status:** Decided

Column-level lineage is derived for SQL and built-in declarative nodes, whose transformation logic can be parsed. Across custom code nodes lineage is task-level only, and the interface shows it as such rather than implying finer detail.

- **Declared mappings.** The author of a custom code node may declare column mappings by hand. The interface labels these as **declared** rather than **derived**, since the platform cannot verify them.
- **Direct only.** Derived lineage covers direct transformations, where an output column's values are computed from identified input columns.

*References:* DE 5.1 · CORE 1.8

#### D11 · Execution modes

**Status:** Decided

The first release has no local, container-free execution mode. All execution runs in containers, and the entry point for evaluation and small teams is a single-machine, container-based deployment of the whole platform.

- **Rationale.** A container-free mode would require an embedded metadata store alongside Postgres, per-node isolated environments for conflicting dependencies, support for additional operating systems, and a permanent obligation to keep two execution paths behaviourally identical. The single-machine deployment is required regardless and adds no cost.
- **Deferred.** Two options are recorded for later: a **local worker** that runs units as processes on a user's machine against a normal control plane, reusing the agent architecture needed for HPC backends; and a **standalone** installation requiring neither a server nor containers. Either is reconsidered if adoption data shows the container requirement is costing users.
- **Seam.** Execution remains behind the backend interface (D12, Seam 9), so a local backend can be added later without changing the model. If one is added, its runs are capped at Traceable, or Re-executable with a recorded lockfile, and may not publish to datasets with an enforced contract. This restriction is to be reconsidered under D36 when a local backend is taken up.
- **Images.** The platform builds images from declared dependencies, with prebuilt base images for Python, R and common scientific tools, so users rarely write Dockerfiles (CORE 1.10).

*References:* CORE 2.9 · CORE 2.15 · CORE 1.10 · CORE 5.4 · DS 1.4

#### D12 · Streaming readiness

**Status:** Decided

Streaming is excluded from the initial scope (D6), but the core model is built so that it can be added without rework. The risk is not missing features; it is assumptions that only hold for finite work being written into schemas, interfaces and state machines. Every design decision is tested against three questions: does it assume execution **terminates**, does it assume input is a **finite snapshot**, and does it assume time means the **wall clock of the run**?

- **Seam 1.** A finite run is one kind of execution, not the only kind. Identity, permissions, monitoring and API routes sit on a neutral execution concept; status vocabularies and schemas are not constrained to terminal states (no mandatory completion timestamp, no success-or-failure-only enum).
- **Seam 2.** The scheduler does not assume tasks end. Health is derived from lease renewal rather than exit status, so an indefinitely running task is representable.
- **Seam 3.** Node types declare which execution modes they support. Every entry reads `[batch]` initially; the field prevents a later restructuring of the palette and allows validation to report a missing streaming implementation.
- **Seam 4.** Every source read records the **range of positions consumed** — snapshot, object version or timestamp now, offsets later — rather than naming a file. Incremental extraction (DE 1.2) requires this regardless, and provenance then generalises to window and offset lineage unchanged.
- **Seam 5.** A dataset version is not defined as a snapshot of a finite table. Datasets are append-only sequences with positions, of which a snapshot is one case and a retained topic another.
- **Seam 6.** Event time is distinguished from processing time. Optional event-time metadata on datasets — timestamp column, allowed lateness — is used by micro-batch immediately and by streaming unchanged.
- **Seam 7.** Reproducibility tiers are defined in terms of **replayable recorded inputs**, not retained files, so retained artifacts and offsets still within a retention window are treated identically, including tier decay on expiry.
- **Seam 8.** Caching is a policy applied to finite outputs behind a strategy interface, not an assumption embedded in dispatch. A unit may legitimately have no cache policy.
- **Seam 9.** The backend interface manages a lifecycle — submit, observe, cancel — with room for optional operations such as upgrade and state snapshot, so a long-lived deployment is another backend implementation rather than a new subsystem.
- **Seam 10.** Task metrics are recorded as time series rather than end-of-run summaries, so lag, watermark skew and backpressure later use the same storage and views.
- **Excluded.** No savepoint or upgrade machinery, state schema evolution, watermark or lateness configuration, exactly-once sink protocols, offset management or streaming connectors. No unified batch-and-streaming abstraction: committing to the intersection of two execution models before either is understood is itself a cost.
- **Cost.** Most seams are field additions and naming discipline. Two require deliberate design: the execution concept (Seam 1) and the input-range model (Seam 4). Untested seams tend to be subtly wrong, so a minimal long-running execution should be implemented as a proof before the model is considered settled. The execution concept of Seam 1 is recorded in D31.

*References:* D6 · D7 · D11 · CORE 1.11 · CORE 2.11 · CORE 3.3 · CORE 4.6 · CORE 5.9 · CORE 6.7 · DE 1.2

#### D13 · Partitioning, intervals and dataset ownership

**Status:** Decided

Partition granularity and logical intervals are user decisions; the platform applies and validates them but never chooses them. Each dataset has exactly one producer. Datasets copied from mutable sources are partitioned by ingestion time at the raw layer and by event time downstream, connected by declared partition dependency functions; whether a source is copied is the author's explicit choice (D35).

- **Ownership.** Partition granularity — daily, hourly, by region, by tenant or none — is a property of the **dataset**, set by its owner. The logical interval — for example “hourly, covering the previous hour” — is a property of a workflow's **schedule**, set by its author.
- **Validation.** The platform checks that interval and partitioning are compatible. An interval equal to or coarser than the partition is accepted. An interval finer than the partition requires the author to declare the partition **open** — appended to by successive runs until explicitly marked complete — so that consumers never mistake a partial partition for a finished one. Boundaries that cannot align are rejected.
- **Timezone.** Timezone is part of both the partition scheme and the interval declaration. A daily partition in UTC and one in Africa/Cairo are different partitions, and a mismatch is rejected rather than silently shifted.
- **Single producer.** Exactly one node in one workflow publishes to a dataset; any number may consume it. Several sources feeding one dataset are combined by a single node. This keeps publication free of races, lineage unambiguous and contract ownership clear, and makes datasets the interfaces between workflows.
- **Time axes.** A dataset extracted from a mutable source is partitioned by **ingestion time**: the raw partition is the only faithful snapshot of what the source held, so downstream reruns read the raw partition and never re-query the source; amended in v0.10 by D35, this applies to copied sources, and an ephemeral source is re-read at run time. Re-extraction is an explicit act that produces a new version of the raw partition. Curated datasets are partitioned by **event time**, because that is how consumers query them, with a declared lateness window.
- **Dependencies.** A node declares how its output partitions depend on its input partitions: identity (the default), a time window such as “the same day to three days later”, all available partitions, the latest partition, or specific values. Where a declared window is too coarse, a merge node may instead discover the affected partitions from the data at run time, at the cost of not knowing the plan in advance.
- **Platform role.** The platform proposes defaults at creation, which the owner confirms — a daily schedule suggests daily partitions, a small dimension table suggests none — and may later advise on granularity from observed partition sizes. It decides physical layout (file sizing, compaction, clustering), which affects performance but not the logical model.
- **Change.** Changing a partitioning scheme is a migration performed by the owner: it produces a new version of the scheme, rewrites history, and requires every downstream dependency mapping to be revalidated. It is never a silent setting change, which is why the default proposed at creation matters.

*References:* D4 · CORE 3.3 · CORE 3.9 · CORE 3.10 · CORE 6.9 · CORE 6.10 · CORE 6.11 · DE 1.7 · DE 2.7 · DE 5.7

#### D14 · Input version resolution

**Status:** Decided

A run resolves the versions of all its inputs once, when it starts, records them, and every node in the run reads exactly those versions. Because every input is resolved at the same instant, a run reads its inputs under snapshot isolation.

- **Pinning.** Any input may instead be pinned to a specific version or snapshot, for example for model training or a reproduction study. Pinned versions are recorded in the same way.
- **Coherent reads.** A user may declare coherent reads for a workflow, with per-input override. The resolver then selects versions that are consistent along lineage — where a run reads both a dataset and something derived from it, the derived version is chosen first and the upstream version that produced it is used. If no coherent set exists, the run fails with an explanation or follows its stale-input policy (D16). This is a configuration of the read model, not a separate feature.
- **Completeness.** Snapshot isolation guarantees a consistent read, not consistent business state. Where inputs must be complete for an interval, partition completion markers (CORE 3.10) and the consumer's stale-input policy (D16) apply.
- **Reruns.** Two distinct actions: **re-execute as recorded** reads the originally resolved versions; **run again on current data** resolves afresh. They are presented separately and never conflated.
- **Retention.** Versions resolved by a run still in progress are protected from garbage collection until the run finishes, so a long run cannot lose its own inputs.

*References:* S9 · CORE 2.16 · CORE 5.10 · CORE 5.11 · CORE 6.5 · D7

#### D15 · Atomic publication

**Status:** Decided

Publication stages new data and then makes it current with a single atomic commit. Consumers never observe a partially applied publication, and a retried attempt never publishes twice.

- **Staging.** An execution unit writes new files to a location scoped to its attempt and never overwrites existing files. Quality gates evaluate the staged data; a failed gate prevents the commit and the staged data becomes a quarantined version, which an override may later release (D31).
- **Commit point.** For managed datasets the platform's metadata catalog is the commit point: one transaction records the new snapshot manifest, and readers resolve files through the catalog rather than by listing storage paths. Where a managed dataset uses a table format such as Iceberg or Delta, that format's own commit is used underneath. This applies uniformly to tabular and non-tabular data.
- **External targets.** Publication to an external warehouse uses the target's own transaction, or a staging table followed by a swap. Where the target cannot commit several partitions atomically, partitions are committed individually and the version is reported as **partially published** rather than concealed.
- **Fencing.** Every commit carries the identity of the attempt that produced it. A late commit from an attempt that was presumed lost and has since been retried is rejected. Orphaned staging files are garbage-collected.
- **Open partitions.** Each append to an open partition is its own atomic commit, and marking the partition complete is a further commit (CORE 3.10).
- **Groups.** By default each dataset commits independently. For managed datasets, an author may declare a **publication group** — for example orders and their order lines — whose members commit together or not at all.

*References:* S10 · D13 · D14 · CORE 2.5 · CORE 6.12 · CORE 6.13 · S12

#### D16 · Input readiness and degraded outputs

**Status:** Decided

Each consumer declares, per input, what happens when that input is stale, failed or missing. Outputs built on inputs that were not ready are marked degraded, and the marking cascades downstream with its reason.

- **Policies.** **Wait** until the input is ready, up to a timeout; **proceed** on the last valid version; **skip** the interval and reconcile later; or **fail** immediately and alert. An input may also be declared optional, in which case the run proceeds without it.
- **Defaults.** Scheduled runs wait with a timeout derived from the freshness expectation of the dataset they produce, then fail and alert. Manual and interactive runs proceed on the last valid version with a warning. Both defaults are configurable per workflow and per input.
- **Waiting.** A waiting run is a scheduler state re-evaluated by the reconciliation loop and holds no compute. Input versions are resolved only once all required inputs are ready, so the snapshot of D14 is taken after the wait rather than before it.
- **Quarantine.** Quarantined versions are never read, whatever the policy, unless an override releases them (D31).
- **Degradation.** An output built on a stale, failed or absent input is published as degraded, with the reason stated — which input, which version was used, and which was expected. The marking cascades to every downstream dataset built from it, carrying the originating cause so that a consumer several steps away sees the root reason rather than only its immediate input. The marking clears when the output is rebuilt from ready inputs.
- **Provenance.** The policy applied, the time spent waiting and the versions ultimately read are recorded in the run's provenance.

*References:* S11 · D14 · CORE 3.11 · CORE 6.14 · DE 4.2 · DE 4.4

#### D17 · Dataset families and first-release scope

**Status:** Decided

Datasets are grouped into families whose behaviour on the platform is the same, rather than handled format by format. The first release supports six families; the remainder are added later through the plugin interface. Amended in v0.10 by D29: the first development slice supports the tabular family only, and the other five follow through the same interface.

- **In scope.** **Tabular** — CSV/TSV, Parquet, ORC, Avro, Arrow, JSON Lines, Excel, statistical-package formats, and Iceberg, Delta and Hudi tables. **Semi-structured and records** — JSON, XML, YAML, logs, and industry record formats such as HL7 and FHIR. **Text and documents** — text corpora, JSONL datasets, and documents requiring extraction such as PDF and DOCX. **Images** — general formats, DICOM, microscopy formats and GeoTIFF, with their annotation formats. **Genomics and life sciences** — FASTQ, FASTA, BAM, SAM, CRAM, VCF, BCF, BED, GFF and related formats, as the demonstration domain. **ML artifacts** — models, training shards, and embeddings and vector indexes.
- **Later.** Audio and video, scientific multidimensional arrays (HDF5, Zarr, NetCDF, FITS), geospatial, graphs, and reports and outputs, delivered through the same interface.
- **Orthogonal.** Compression and archive wrappers — gzip, zstd, bgzip, tar, zip — apply across families rather than forming a family of their own.
- **Follows.** Supporting these families requires five structural capabilities: file groups whose members travel together (CORE 6.16), linked items such as paired reads (CORE 6.17), sharded collections of many small items (CORE 6.18), declared splittability (CORE 6.19), and classification that reaches metadata embedded inside files (DE 5.10).
- **Models.** Models are a specialised dataset type rather than a separate registry. They share identity, versioning, lineage, publication, retention, classification and erasure with every other dataset, and add a signature, a lifecycle stage, evaluation metrics and approval state. The registry interface presents them as models; underneath they are the same aggregate, so one lineage graph runs from source data to model.
- **Extension point.** Each family is implemented through one interface covering nine responsibilities: describe (file groups and links), contract, validate and metadata, which are required; and profile, preview, compare, canonicalise and access, which are optional and degrade gracefully when absent. The platform core never interprets a format directly.
- **Placement.** Family plugins read bulk data and therefore run in the data plane, inside execution units; only their results reach the control plane. Third-party plugins are sandboxed like any other user code.
- **Release.** The interface is internal in the first release. The six built-in families are implemented against it, and it is published as a stable plugin API only once it has held up.

*References:* S12 · CORE 5.8 · CORE 6.3 · CORE 6.15 – 6.19 · DE 5.10 · MLE 3.2

#### D18 · Format types, plugin implementations and bindings

**Status:** Decided

A data format is a **type** defined once by the platform; plugins are **implementations** of a type. Every dataset is bound to exactly one pinned implementation. Several implementations and versions of a type may coexist in the architecture, but by policy a project uses one per type unless an administrator allows more.

- **Plugin kinds.** Two kinds of plugin exist, both of which may come from third parties: **dataset-family plugins**, which describe what data is, and **node plugins**, which describe what is done to it. Connectors to source and target systems are node plugins.
- **Type.** A namespaced identifier with a specification version, such as `genomics/bam` v1, reusing established vocabularies such as the EDAM format ontology where they exist. The type owns three things: the **contract schema** (what a contract for this format may state), the **reader protocol** nodes program against, and a **conformance suite** of files that must validate, files that must fail, and pairs a comparator must judge equivalent or different.
- **Manifest.** A plugin declares its identity and version, the type and type version it implements, its pinned runtime image, the file-group layout of one item (roles and filename patterns), any linked items, and which optional capabilities it provides — including splittability.
- **Functions.** A plugin implements `validate` and `metadata`, which are required, and optionally `profile`, `preview`, `compare`, `canonicalise`, `open` (a reader conforming to the type's protocol) and `splits`. A plugin providing only the required functions is fully usable; absent capabilities degrade to file listings, byte-level comparison, input-addressed caching and whole-file processing.
- **Boundaries.** A plugin receives items and returns structured results. It does not define contract schemas or reader protocols, access the catalog or other datasets, manage storage, credentials or commits, or render interface elements; previews are returned as structured data of a fixed kind and drawn by the platform.
- **Nodes.** Node ports declare types, never plugins. A node therefore works with any dataset of the declared type regardless of which implementation validated it.
- **Binding.** Each dataset is bound to one implementation at an exact version, recorded on every dataset version. Changing the implementation is an explicit migration that revalidates the dataset. A dataset shared with another project is read using its own binding, whose pinned image remains available.
- **Policy.** Administrators set the allowed implementations per type at organisation or project level, defaulting to exactly one. New datasets bind automatically to the approved implementation, so ordinary users are never asked to choose. Additional implementations may be allowed for vendor transitions or partner-supplied data.
- **Conformance.** A plugin must pass the type's conformance suite to claim the type. The suite bounds how far implementations may disagree about validity and equivalence; they may still differ in performance, preview quality and additional statistics.
- **Upgrades.** Upgrading a binding to a newer plugin version is explicit but inexpensive: a bulk action revalidates the selected datasets and reports any whose outcome would change before the switch is committed.
- **Later.** Taking presentation capabilities (preview, profile) from a different implementation than the semantic ones (contract, validation, comparison, hashing) is excluded from the first release.

*References:* D17 · CORE 1.2 · CORE 1.9 · CORE 6.20 · CORE 6.21 · CORE 6.22 · S20

#### D19 · Stable dataset identity

**Status:** Decided

Dataset names are fixed in the first release: a dataset cannot be renamed or moved to another project. Every dataset also carries an immutable internal identifier, which lineage, bindings, consumer registrations, provenance and cache keys reference, so that renaming can be introduced later without migration.

- **Structure.** Names take the form `project.path.name`, for example `analytics.curated.customers`. The project segment is the namespace and permission boundary; intermediate segments are free-form and follow the project's own conventions. Within its project a dataset may be referred to by its short name.
- **Rules.** Lowercase letters, digits and underscores, separated by dots, with a length limit. Uniqueness is case-insensitive.
- **Display title.** A mutable display title covers cosmetic changes without affecting the name used in definitions.
- **No reuse.** The name of a deleted dataset is never reused automatically; reuse requires explicit administrator confirmation. This prevents a workflow from silently reading a different dataset under a familiar name.
- **Scope.** The same rules apply to workflows. Projects carry display titles, since teams are renamed more often than datasets.
- **Later.** Renames with aliases, reference-updating tooling and transfers between projects are deferred, and can be added because identity is already separate from name.

*References:* S13 · CORE 6.1 · CORE 1.6

#### D20 · Backfill commits and scheduling

**Status:** Decided

A backfill commits each logical interval as it completes, while downstream reconciliation is deferred and planned once over everything the backfill changed. Restatements may instead be committed atomically. Backfills run at lower priority than scheduled work.

- **Scope.** These are data commits in the platform catalog (D15), not version-control commits of workflow definitions. Each data snapshot nevertheless records the definition version that produced it.
- **Per interval.** By default each interval is committed when it finishes, so progress is visible, a failure affects only its own interval, and the backfill resumes from the first incomplete interval.
- **Coalescing.** While a backfill runs, the reconciler holds downstream work and plans it once — when the backfill completes, or at batch boundaries for long backfills — over the union of changed partitions. Without this, a lateness window causes each downstream partition to be rebuilt several times.
- **Restatement.** A backfill that recomputes existing partitions with changed logic may be declared atomic: every interval is staged and a single snapshot is committed at the end, so consumers never observe a mixture of old and new logic. Gap-filling backfills do not need this.
- **History.** Commits made by one backfill carry its identifier, so version history presents the backfill as a single collapsible entry.
- **Priority.** Backfills run below scheduled runs under fair scheduling (CORE 3.6), so a long backfill never delays current pipelines. Writes to the same partition are serialised, so a backfill and a scheduled run cannot collide.

*References:* S14 · D13 · D15 · CORE 3.4 · CORE 3.6 · CORE 3.12 · CORE 3.13

#### D21 · Architecture planes

**Status:** Decided

The platform is divided into four planes — interface, control, data and observability — each with a single responsibility and trust level. Storage systems are assigned to planes. The division is illustrated in the Architecture section.

- **Invariants.** Bulk data never passes through the interface or control planes. Untrusted code runs only in the data plane. Any data-plane component may be terminated at any moment without loss of correctness. Correctness never depends on observability.
- **Protocol.** The control plane leases work to the data plane with scoped credentials and a fencing token; the data plane returns heartbeats, events and commit requests; only the control plane makes a result current.
- **Failures.** A control-plane outage stops new dispatch and commits but not running work; a lost data-plane node is recovered by lease expiry and retry; an observability outage affects no decision.

*References:* D12 · D15 · D22 · CORE 2.11 · CORE 4.1

#### D22 · Deployment topologies

**Status:** Decided

Four options are supported, ordered by how much the customer controls: **fully managed** (vendor operations, compute and storage); **managed with customer storage** (vendor operations and compute, writing to the customer's storage); **hybrid** (interface and control planes hosted by the vendor, data plane and storage in the customer's own cloud account or HPC cluster); and **self-hosted** (the customer operates everything, on one machine or a cluster).

- **Distinction.** With customer storage but vendor compute, data still passes through the vendor's machines during processing. This addresses integration, cost and lock-in, but strict sovereignty requires the hybrid option.
- **Outbound only.** Data-plane execution agents connect outward to the control plane and pull work. No inbound connectivity into a customer network is ever required. The control-to-data protocol must therefore work across networks, tolerate latency and interruption, and be pull-based. Amended in v0.10 by D29: the same pull-based agent is used in every topology, including self-hosted and single-machine deployments.
- **Credentials.** In the hybrid topology, credentials for customer storage are minted inside the customer's environment by the agent. The hosted control plane never holds them.
- **What crosses.** Only metadata, statistics, events and pre-computed previews cross to the hosted planes. Previews and samples obey the classification of their source dataset, and a customer may disable them for sensitive datasets.
- **Telemetry.** A customer may keep logs and metrics within its own environment, with live tailing proxied through the agent, because logs may contain sensitive content.
- **Primary model.** Bring-your-own-compute is the primary model: execution runs on the customer's own infrastructure and the vendor coordinates. Hybrid and self-hosted are the first-class topologies. Fully managed serves trials and small teams, and managed with customer storage is retained unchanged. Added in v0.9.
- **Compute.** A bring-your-own-compute deployment provides a container-capable backend: Kubernetes, cloud batch or an HPC cluster. A warehouse alone runs only pushdown work; in-process nodes on DuckDB or Polars, Python code nodes and command-line tools require container compute. A warehouse-native container service may later serve as a backend for customers whose only compute is a warehouse.
- **Images.** Image builds and the image registry may run in the customer's environment, and images are referenced by digest wherever they are stored (CORE 1.10, CORE 5.1). HPC clusters commonly run images through Apptainer rather than Docker.

*References:* D5 · D9 · D11 · D21 · D25 · D28 · CORE 1.10 · CORE 2.18 · CORE 2.25 · CORE 4.7 · CORE 4.8 · CORE 7.7

#### D23 · Artifact storage layout

**Status:** Decided

Artifacts are stored at identity-addressed paths, and the artifact itself is a manifest in the catalog. Content hashes are attributes of an artifact rather than the basis of its location.

- **Paths.** Files are written directly to `artifacts/<tenant>/<project>/<artifact-id>/…`, with the identifier assigned before writing. Content-addressed paths would require a hash before the final location is known, and therefore a second write for large outputs, since object stores have no inexpensive rename.
- **Manifest.** Each artifact's catalog record lists its files with their byte digests and file-group roles (D17), its schema, statistics (byte and row counts per partition being mandatory, D34) and partition values, a canonical hash where under the D8 threshold, its preview reference, the producing task run and its storage target (D4).
- **Immutability.** Files are never overwritten; any change produces a new artifact.
- **Deduplication.** Optional and asynchronous: where byte digests match, a later manifest may reference an earlier artifact's files and the duplicate is removed.
- **Collection.** Garbage collection marks everything referenced by a retained, cached, pinned or provenance-protected manifest, and removes the rest. Provenance protection beyond ordinary retention applies only where the reproducibility setting is on (D36).
- **Layers.** A dataset snapshot references partition versions, which reference artifact manifests, which reference files. Where the storage target is an Iceberg or Delta table, that table's own metadata serves as the manifest.

*References:* D4 · D8 · D15 · D17 · CORE 6.2

#### D24 · Dataset materialisation requests

**Status:** Decided

Alongside running a workflow, a user may ask for a dataset to be made current through a given time. The reconciler derives and runs the minimum work required. In the first release such requests are confined to a single project.

- **Two entry points.** **Imperative**: run workflow W for interval X. **Declarative**: make dataset Y current through time T, where the reconciler decides what runs from dataset state, dependency functions and readiness policies.
- **Planning.** The planner operates on the dataset graph of the project, which may span several workflows.
- **Grouping.** A materialisation request is a first-class entity grouping every run it causes, so that the reason any run occurred can be traced back to the request that caused it.
- **Interface.** The catalog offers refresh actions with explicit build modes — only this dataset; upstream where modified; all upstream; downstream — and shows stale state.
- **Later.** Requests that cross project boundaries, where execution rights must be resolved against the producing team's policies, and freshness policies that the reconciler enforces automatically in place of schedules.

*References:* D13 · D16 · D20 · CORE 3.5 · CORE 3.14 · CORE 3.15

#### D25 · Processing engines and runtimes

**Status:** Decided

The runtime is a property of the node type. Built-in relational nodes are defined once, as Ibis expressions (D27), and run on DuckDB inside an execution unit or are pushed down to a warehouse; other built-in tabular nodes are implemented in Polars and run in-process only; non-tabular families run in container runtimes and scale by fan-out. Placement follows where the data lives, not how large it is. Amended in v0.10: built-in tabular nodes are Ibis first, with Polars by justified exception (D27), and each unit's working set is checked against backend capacity (D34).

- **Layers.** The **backend** (Kubernetes, HPC agent, cloud batch) decides where units run; the **runtime** (SQL, Polars, Python, container command) decides what runs inside a unit and is declared by the node type, including third-party node plugins (D18); the **tools** are the libraries and binaries in the node's image. Only the runtime varies with the kind of data.
- **Built-ins.** Each built-in node has exactly one implementation. Nodes intended for pushdown — filter, select, join, aggregate, window, union, sort, deduplicate and pivot with fixed columns — are written in SQL. Nodes more naturally expressed as dataframe code — resample, fill, fuzzy matching, pivot over data-dependent values, sequential and stateful logic, parsing — are written in Polars and are never pushed down. Moving a node from one group to the other is a new node version. Amended by D27: nodes intended for pushdown are defined as Ibis expressions rather than SQL text, and this group absorbs operations previously assigned to Polars wherever Ibis can express them. Amended again in v0.10 by D27: Ibis on DuckDB is the engine for every built-in node, and a built-in node is implemented in Polars only by justified exception.
- **Dialects.** SQL nodes use the portable subset of SQL and are translated per dialect (for example with SQLGlot). A node that relies on dialect-specific constructs declares the dialects it supports. Under D27 this compilation is performed by Ibis, which itself uses SQLGlot.
- **In-process.** DuckDB and Polars run together in one process inside a unit and exchange data as Arrow. Consecutive nodes on the same engine are chained into one **engine segment** — a single DuckDB query or Polars lazy plan — so each optimiser sees the whole segment; data changes hands only at segment boundaries. Heavy joins and aggregations fall to DuckDB, which spills to disk. Memory and thread limits for both engines are set from the unit's resource allocation, and DuckDB's spill directory is sized from it in the same way (D34).
- **Selection.** Precedence: explicit override, then hard constraints (restricted data may not leave its warehouse; placement and residency; deferred from the first release, D26), then dialect capability, then data location. Relational nodes whose inputs share one warehouse are pushed down; inputs in files, object storage or uploads are processed in-process. At the first Polars node after warehouse data, the planner pushes down everything before it and extracts the reduced result.
- **Size.** Size does not select the engine. Extraction is capped by a configurable limit, and a plan that exceeds it asks the author instead of proceeding. An opt-in cost policy may prefer a cheaper placement, and a single-node guideline flags work beyond in-process capacity. Amended in v0.10 by D34: the single-node guideline becomes a capacity check in the plan; and once an engine is added that reads the same location as the in-process engines, such as Spark, the choice between engines at one location is made by capacity.
- **Data movement.** Data moves only out of warehouses into execution units, never into a warehouse. Where a node's inputs sit in different locations, each warehouse's share of the work is first reduced by pushdown and the reduced results are processed in-process. The planner writes to a warehouse only to publish a dataset whose storage target is that warehouse (D4, D15). Where data held elsewhere forces a large extraction, the plan suggests giving that data the warehouse as its storage target, which makes the work eligible for pushdown; the planner never moves it on its own. Revised in v0.9: previously the smaller input was staged into the warehouse.
- **Repartition.** Where a node must group by a key other than the partitioning of its input, for example a fill-forward per customer over data partitioned by day, the planner inserts a repartition step: a unit that rewrites the data hash-bucketed by that key, after which the node fans out per bucket. The key is taken from the grouping the node declares. This provides the shuffle that a distributed engine would otherwise supply, without one. Work that cannot be divided by any key, such as a global sort or a join of two very large tables that cannot be bucketed to match, remains flagged by the capacity check (D34). Added in v0.9.
- **Visibility.** The plan shows each unit's engine, location and the reason for the choice before the run starts. Users do not choose engines for built-in nodes.
- **Correctness.** Every Ibis and SQL node is conformance-tested against DuckDB and each supported warehouse dialect, since translation can change behaviour around nulls, casts, timestamps and float aggregation. The engine family forms part of the cache key.
- **Warehouses.** The first release pushes down to Postgres and Snowflake. Further warehouses are added in later releases. Amended in v0.10 by D29: the first development slice runs everything in-process on DuckDB and Polars; pushdown follows.
- **Code nodes.** SQL and Ibis (both eligible for pushdown, D27), Polars and pandas (in-process), and container commands for command-line tools such as samtools, BWA and GATK. All are supported on equal terms; none is designated the default. Revised in v0.10: Polars was previously the recommended default for Python.
- **Non-tabular.** Semi-structured data uses SQL where DuckDB handles it and Python otherwise (XML, HL7, FHIR). Text, images and ML artifacts run in Python runtimes, with GPUs where declared. Genomics runs as container commands, often on HPC agents. These scale by fan-out over items, partitions or splits (CORE 6.18, CORE 6.19). Tabular data crosses unit boundaries as Arrow-readable files; other data crosses as artifact manifests.
- **Later.** Spark as a plugin executing against customer-operated clusters; Flink if streaming is added (D6, D12), and Ray for distributed Python and ML workloads, likewise against customer-operated clusters (D22).

*References:* D3 · D10 · D17 · D18 · D21 · D26 · D27 · D28 · S6 · S24 · CORE 1.8 · CORE 1.12 · CORE 2.19 · CORE 2.20 · CORE 2.26 · DE 2.1 · DE 2.2

#### D26 · Placement constraints

**Status:** Decided

Placement constraints, the hard requirements and soft preferences that govern where an execution unit runs, are deferred from the first release. Until they are introduced, the planner places units by the rules of D25 alone, and the hard-constraint step of its selection precedence is empty. Three requirements are kept from the outset so that constraints can be added later without rework and without losing the ability to judge historical runs and data against them.

- **Deferred.** An optional block of placement requirements and preferences in the IR; residency and data-movement rules declared on datasets; resolution of constraints by the planner, with rejection of plans whose hard constraints cannot all be met; and handling of units whose constraints cannot be met by currently available capacity.
- **Seam 1.** **Location record.** Every attempt records the backend and region in which it ran, and every artifact manifest records a storage location specific enough to identify its region (D23). This record cannot be reconstructed afterwards: without it, artifacts produced before constraints exist could not be judged against a residency rule introduced later and would all have to be treated as ineligible.
- **Seam 2.** **Cache eligibility.** A cache lookup finds a candidate under its key and then applies eligibility checks before the output is reused. The permission check of D9 is the first such check; a placement check is later added as a further check without changing the cache.
- **Seam 3.** **Explicit placement.** The planner decides every unit's backend and location and records the reason (D25), including where the reason is only the default. No backend selects a location that the planner cannot see or override.
- **Considered.** Discussed before deferral and not decided: deriving most hard constraints from the policy of the datasets a unit reads rather than requiring node authors to declare them; limiting node-level requirements to properties of the computation, such as an accelerator or a tool licensed on one cluster; expressing requirements in the IR as abstract labels resolved through environment bindings rather than as concrete regions; and treating a cached output stored in a location that violates a run's constraints as a miss.
- **Transition.** Workflows built before constraints exist may depend on unrestricted data movement and fail to plan once constraints apply. A warning-only phase before enforcement was raised as the likely remedy and is not decided.
- **Open items.** S6 and S23 remain open and are deferred with this decision.

*References:* D9 · D21 · D22 · D23 · D25 · S6 · S23 · CORE 2.9 · CORE 2.19 · CORE 2.21 · CORE 2.22

#### D27 · Ibis for relational node definitions

**Status:** Partly decided

Built-in relational nodes are defined as **Ibis** expressions rather than as hand-written portable SQL. Ibis compiles each expression into the dialect of the engine that runs it: DuckDB inside an execution unit, or the warehouse when the node is pushed down. Ibis is an API above the engines, not an engine; DuckDB remains the in-process engine. The same API is offered from the first release as a code node for Python authors whose transformations should be eligible for pushdown, which D25 had deferred.

- **Amends.** D25. The split between built-in nodes becomes Ibis, eligible for pushdown, and Polars, in-process only. The SQL group of D25 is replaced by the Ibis group.
- **Ibis group.** Every built-in node that can be expressed as an Ibis expression. This includes operations previously assigned to Polars because they are awkward in portable SQL, such as fill-forward and fill-backward through window functions, pivots and date arithmetic, so less data needs to be extracted from a warehouse. The final assignment of each node is made when the built-in palette is designed.
- **Ibis first.** Amended in v0.10: Ibis on DuckDB is the engine for every built-in node, and Polars is an exception rather than half of the palette. A built-in node is implemented by the first of four tiers that can express it: a portable Ibis expression, eligible for pushdown to every supported dialect; an Ibis expression calling a native backend function through a builtin UDF, such as DuckDB's string-similarity functions, eligible for pushdown only to dialects that declare an equivalent; an Ibis expression with a vectorised PyArrow UDF, in-process only but still inside the DuckDB segment, so that the surrounding joins and aggregations keep spilling to disk; and, by justified exception, a Polars implementation. Fuzzy matching and complex parsing therefore move to the Ibis tiers.
- **Polars group.** Reduced in v0.10 to justified exceptions, chiefly logic in which each row depends on the result computed for the previous row, which window functions cannot express and Ibis does not support through recursive queries. Code nodes are unchanged: Ibis, Polars and pandas are all supported.
- **Order and spilling.** Since SQL engines have no row order, every node whose result depends on order declares a sort key. DuckDB does not spill `PIVOT`, `list()`, `string_agg()` or ordered aggregates to disk; nodes using them declare the non-spilling memory class (D34).
- **One definition.** The Ibis expression is the single definition of a node; compiled SQL is derived from it. Engine segments are preserved, since a chain of Ibis nodes compiles to a single query.
- **Conformance.** The conformance matrix is retained (CORE 1.12). Where Ibis does not support an operation on a backend, the node declares that dialect unsupported and is not pushed down to it.
- **Versioning.** An Ibis upgrade can change compiled SQL, so the Ibis version forms part of the node version and is pinned in the node's image.
- **Lineage.** Column-level lineage for these nodes may be derived from the Ibis expression tree rather than by parsing SQL (D10).
- **Compilation.** Ibis compiles inside execution units, in Python. The planner needs only to know whether a node is eligible for pushdown and which dialects it supports, so the choice of control-plane language is not constrained.
- **Rejected.** Replacing DuckDB with Ibis's Polars backend for local execution. DuckDB documents out-of-core grouping, joining, sorting and windowing, while Polars' streaming engine processes data in batches without documented spilling of operator state; Ibis on DuckDB compiles to SQL, the same path used for Postgres and Snowflake, which eases conformance; and DuckDB is Ibis's default and most complete backend. The objection that Polars is present in any case no longer applies once built-in nodes are Ibis first.
- **Condition.** Confirmed subject to a spike. Revised in v0.10: the spike classifies each candidate built-in node into one of the four Ibis-first tiers, producing the list of Polars exceptions; runs the nodes on DuckDB, including joins, aggregations, sorts and windows larger than memory under a fixed memory limit; checks that the nodes compile for Postgres and Snowflake, with execution against those warehouses following pushdown (D29); and reviews the maintenance and release practices of the Ibis project, which becomes a core dependency. Coverage gaps are reported before the palette is designed.
- **Deferred.** Checking that the palette also compiles on Ibis's PySpark backend is deferred until a Spark engine is taken up (D25).

*References:* D10 · D25 · CORE 1.8 · CORE 1.12 · CORE 2.19 · CORE 2.20 · DE 2.1 · DE 2.3

#### D28 · Warehouse connection policy and plan pinning

**Status:** Decided

The planner chooses placement automatically, within a policy set on each warehouse connection by the warehouse's owner. Workflow authors may pin the plan of a production workflow so that a change of placement is reported rather than applied.

- **Roles.** The **warehouse owner** sets the connection policy. The **workflow author** sets explicit overrides (D25) and may pin a plan. The **planner** places every unit automatically within both.
- **Policy.** Each warehouse connection states whether the platform may compute in that warehouse, which of the warehouse's compute clusters it uses and at what size, and an optional credit budget, whose enforcement is defined together with cost attribution (S22).
- **Read-only.** A connection without compute rights makes pushdown unavailable for that warehouse. The planner then extracts within the configured cap or asks the author (D25).
- **Defaults.** A new connection allows compute once its owner names a compute cluster, which Snowflake requires for any query. No budget is set by default.
- **No staging.** The policy has no setting for staging data into the warehouse, because the planner writes to a warehouse only to publish a dataset whose storage target is that warehouse (D25).
- **Tagging.** Every query the platform runs in a warehouse carries a tag identifying the platform, workflow and run, so that it appears as such in the customer's own query history. Warehouse usage is reported per workflow (CORE 4.5, S22). The same applies to every customer backend: jobs on Kubernetes, cloud batch and HPC carry equivalent labels, so that all compute the platform causes on customer infrastructure is attributable (D22).
- **Selection.** Connection policy enters the selection precedence of D25 at the dialect-capability step: a connection without compute rights is treated as an unavailable dialect. It does not reopen the hard-constraint step deferred by D26.
- **Pinning.** An author may pin the plan of a workflow. Each run compares its placement with the pinned plan and keeps the pinned placement where it remains possible; a difference is reported to the author. If the pinned placement can no longer be honoured, for example because a connection has become read-only, the run stops before execution with an explanation until the author accepts a new plan.

*References:* D21 · D22 · D25 · D26 · D27 · S22 · CORE 2.19 · CORE 2.23 · CORE 2.24 · CORE 4.5 · CORE 4.8

#### D29 · First development slice

**Status:** Decided

Development begins with a deliberately narrow slice of the catalogue: the tabular family, the single-machine container deployment and Kubernetes, in-process execution on DuckDB through Ibis with Polars by exception, the visual canvas and round-tripping to text in git. Added in v0.10.

- **Data.** The tabular family only (D17). File groups, linked items, sharded collections and splittability (CORE 6.16 – 6.19) are therefore not required in the first slice. The other five families follow through the same family interface.
- **Backends.** The single-machine container deployment (CORE 2.17) and Kubernetes. HPC agents and cloud batch follow.
- **Engines.** In-process only (D25): Ibis on DuckDB for every built-in node, with Polars by justified exception and for code nodes (D27). Built-in nodes are defined as Ibis expressions so that they need no rewriting when pushdown is introduced. Warehouse pushdown, the warehouse connection policy (D28), Spark and Flink follow.
- **Authoring.** The canvas (CORE 1.1) and round-tripping to text in git (CORE 1.6) are both in the first slice, so the canonical text syntax is settled together with the IR specification.
- **Agent.** The data plane is driven by a pull-based execution agent in every deployment, including single-machine and self-hosted ones; the control plane never calls a backend's API directly. Hybrid deployment then differs only in where the control plane runs, not in how work is executed (D22).
- **Licence.** The repository is private. The licence is chosen before it is made public or accepts external contributions, in line with D5.

*References:* D5 · D11 · D17 · D22 · D25 · D27 · D28 · CORE 1.1 · CORE 1.6 · CORE 2.9 · CORE 2.17 · CORE 2.18 · CORE 6.15

#### D30 · Tenancy and isolation enforcement

**Status:** Partly decided

Isolation of tenants and projects is enforced throughout the codebase from the first slice, including in single-tenant self-hosted installations, rather than being added with the cloud edition. The tenant identifier on every entity (D5) is necessary but not sufficient: every path through which an entity is read, written, cached or leased checks its scope. Added in v0.10.

- **Persistence.** Every query is scoped by tenant and project. No data access path is unscoped.
- **Interface.** Every request is authorised against the caller's roles in the project concerned.
- **Storage.** Artifact paths are prefixed by tenant and project (D23), and credentials leased to a unit are scoped to that unit (D21).
- **Cache.** Lookups are scoped to the project by default and pass through the eligibility filter (D9, D26).
- **Agents.** Each agent's identity is bound to one tenant, and an agent leases only that tenant's work.
- **Visibility.** Entities a user cannot read are hidden by default, in the catalogue, in lineage and in previews. Showing more later, such as anonymous placeholders in lineage, is additive and is settled with S19.
- **Open.** The enforcement mechanism — Postgres row-level security or a mandatory scoping layer in the application — and the role model, to be settled with the control-plane design.

*References:* D5 · D9 · D21 · D23 · D26 · S19 · S20 · CORE 7.1 · CORE 7.3 · CORE 7.6 · CORE 7.7

#### D31 · Execution state model

**Status:** Decided

Execution is recorded at three levels: the **run** (one execution of a workflow version for a trigger and a logical interval), the **task run** (one execution of a unit at an index path such as `map[17]` or `loop[3]/map[2]`) and the **attempt** (one try at a task run, holding the lease and fencing token). Added in v0.10.

- **Phase and outcome.** Each level carries a lifecycle phase — pending, active, suspended or ended — and, separately, an outcome that remains empty until the phase is ended. Finer states, such as a task run being ready, dispatched, running or committing, are sub-states within a phase. No level assumes that it will end, as D12 Seam 1 requires.
- **Outcomes.** A run ends succeeded, failed, cancelled or skipped. A task run ends succeeded, failed, cancelled, skipped or reused. An attempt ends committed, failed, lost, cancelled or fenced. A conditional branch not taken ends as skipped with its reason. Degradation is not an outcome: it is a property of outputs and dataset versions (D16).
- **Waiting for inputs.** A sub-state of the run's pending phase that precedes input resolution, holds no task runs and no compute, and is re-evaluated by the reconciler. When the wait times out, the readiness policy of D16 applies; by default a scheduled run then fails and alerts (D14, D16).
- **Approval.** An approval node's task run enters a suspended state awaiting approval, holds no lease, and is resumed externally through the API. Gated publication uses the same state on its commit step, with the staged data held (CORE 6.8, MLE 3.4).
- **Quality-gate hold.** A failed gate quarantines the staged data (D15), and downstream task runs are held rather than failed or retried (DE 4.4). The hold has a configurable timeout, after which the run ends as failed with the reason that an upstream gate failed. The timeout bounds how long D14's protection of resolved inputs can pin storage. Who may override is S18.
- **Override.** An override releases the quarantined version: it is an act on a dataset version, protected by the version's quarantine state, not a continuation of the run. Within the hold, the release commits the version and the held task runs resume in the same run, whose resolved inputs are still protected. After the timeout, the release is a publication act alone: no continuation run is started, the downstream datasets become stale because their upstream has a new version (D13), and they are rebuilt on current data by normal scheduling or a materialisation request (D24) under each consumer's readiness policy (D16). A released version older than the current version is recorded in history but does not become current. A quarantined version is retained until it is released, explicitly discarded or its quarantine retention expires, whose default belongs with S15. Provenance records who released the version and when, its producing run and the gate verdict overridden; if that run's inputs are later collected, it decays to Traceable as any run would (D7). Re-executing the original run as recorded (CORE 2.16) remains available while its inputs are retained.
- **Failure classes.** An attempt that ends failed records a class: infrastructure, resource exhausted, timeout or task error. Infrastructure failures and lost attempts draw on a platform retry budget, separate from the author's retry policy, which governs task errors (CORE 2.5). A fenced attempt is not a failure: a newer attempt has superseded it. Resource exhaustion is a distinct class so that memory escalation (S8) can be added without a schema change. Health is derived from lease renewal (D12, Seam 2).
- **Checkpoint slot.** Every task run has an optional checkpoint slot, scoped to the task run rather than the attempt. A unit may write to it; its commits are fenced like any other; the next attempt receives the latest checkpoint. The platform does not interpret its contents, and provenance records when an attempt resumed from a checkpoint. This covers long-running training (MLE 2.3), resumption after reclamation of spot capacity (MLE 2.4) and resumption of a partially completed extraction (DE 1.5) without a separate task kind.
- **Nested workflows.** A node that references another workflow is inlined into the parent run at compile time, pinned to a version of the referenced workflow, and each resulting task run records its origin so that the interface can group them. A separate child run would resolve its inputs at a different instant and break snapshot isolation (D14).
- **Cache hits.** A unit served from cache is recorded as a task run with the outcome reused, a reference to the task run whose output was reused, and no attempts (CORE 2.13).
- **Pause and cancel.** Pausing stops dispatching new task runs and lets running attempts finish, after which the run is suspended until resumed; cancelling signals running attempts at their next heartbeat (CORE 2.8).
- **Deferred.** Whether the task runs of a large map are created up front or in batches as they are dispatched is settled with scheduler capacity (S4).

*References:* D2 · D7 · D12 · D13 · D14 · D15 · D16 · D24 · S4 · S8 · S15 · S18 · CORE 1.4 · CORE 2.5 · CORE 2.8 · CORE 2.11 · CORE 2.13 · CORE 2.16 · CORE 6.8 · DE 1.5 · DE 4.4 · MLE 2.3 · MLE 2.4 · MLE 3.4

#### D32 · Execution unit structure

**Status:** Decided

An execution unit is one container running one image, with one resource request and one attempt lifecycle, reading its inputs from storage and writing its outputs to storage. Inside it, nodes are grouped into **engine segments** — consecutive nodes on one engine — which hand data to each other in memory as Arrow. Work is therefore described at three levels: the node (what the user draws), the segment (what one engine executes) and the unit (what the orchestrator dispatches). Added in v0.10.

- **Amends.** The key terms and D25: a unit was described as "one image, one process" whose nodes share a runtime, while D25 and its worked examples placed several engines in one unit. The runtime is now a property of the segment, and the fusion condition "share a runtime" becomes "share an image and execution location".
- **Segment kinds.** A DuckDB query compiled from Ibis, including any vectorised PyArrow UDFs it calls (D27); a Polars lazy plan; or a Python block. A warehouse query is added as a further kind when pushdown is introduced.
- **Binding.** Ibis nodes are defined on unbound tables, carrying a schema and a name but no data or connection. The unit runtime binds them at execution time, registering the unit's inputs on an in-process DuckDB connection, or, once pushdown exists, on a warehouse connection. Whether a node is pushed down is therefore decided by the planner at binding, not by how the node is written (D25).
- **Container commands.** A node that runs a command-line tool is always a unit of its own, since the tool is the process.
- **Code nodes.** A Python code node runs in the image built from its declared dependencies (CORE 1.10). It may share a unit with built-in nodes only when that image is built on the platform's base image, as platform builds are by default.
- **Pushdown.** When introduced, the unit's runtime submits the warehouse query and streams its result into the next segment. A fully pushed-down unit is a unit with a single warehouse segment. The model does not change.

*References:* D1 · D25 · D27 · CORE 1.10 · CORE 2.14 · CORE 2.20 · DE 2.1

#### D33 · Automatic fusion

**Status:** Decided

Fusion is fully automatic from the first slice. The planner separates **legality** — whether nodes may share a unit — from **policy** — which of the legal groupings to choose. Added in v0.10; amends D1.

- **Composition is separate.** Composites are flattened before fusion is planned. A composite may become one unit, several units, or part of a unit shared with nodes outside it; composition never implies fusion.
- **Legality.** The fusion conditions in the key terms: a shared image and execution location (D32), compatible resources, no control flow between the nodes, no output that must be stored, no external side effect, no node marked to run as its own unit, and no cycle between units. Legality is deterministic and needs no run-time measurements.
- **Policy.** Behind a replaceable interface. The first-slice policy fuses as far as legality allows, subject to guard rails: a unit's resource request may not exceed a configurable ceiling, and independent branches are not fused where doing so would give up their parallelism across machines. Later policies may use measured cost and change frequency from run history.
- **Manual control.** Users can only split: pin a cache boundary, or mark a node to run as its own unit (CORE 2.13). A manual control to fuse would add nothing, since the policy already fuses wherever fusion is legal.
- **Determinism.** The same IR under the same policy version always yields the same units, and every plan records the policy version, which plan pinning (D28) and reproducible plans rely on. Because cache keys are chained through nodes (D8), a change of policy does not invalidate cached outputs.
- **Development runs.** Runs on samples during development execute unfused, retaining every intermediate (CORE 6.6).

*References:* D1 · D8 · D28 · D32 · CORE 1.4 · CORE 2.13 · CORE 2.14 · CORE 6.6

#### D34 · Capacity and size

**Status:** Decided

No maximum size is declared on datasets. Capacity is not a property of a dataset but of the operation, the data and the resources of the unit that runs it: a filter streams through any volume, a large join or aggregation is bounded by disk and time once DuckDB spills, and a non-spilling operation is bounded by memory. Because most units process one partition or one bucket (D13, D25), the size that matters is each unit's input slice. The planner therefore observes sizes and checks them against capacity. Added in v0.10.

- **Observed sizes.** Byte and row counts per partition are mandatory statistics on every artifact manifest (D23). Sizes of outputs not yet produced are estimated from upstream statistics or the previous run, and marked unknown where neither exists.
- **Memory class.** Every node type declares a memory class — streaming, blocking and spilling, or blocking and non-spilling — as part of the node-type contract.
- **Capacity ceilings.** Administrators declare, per backend, the largest memory and ephemeral disk a single unit may be granted.
- **Capacity check.** The planner estimates each unit's working set from observed sizes and memory classes and compares it with the ceiling. Where it does not fit, the planner repartitions and fans out if the node declares a grouping key (D25, CORE 2.26), otherwise requests a larger allocation up to the ceiling, and otherwise flags the unit before the run with its reason. The result is recorded in the plan like any placement (D26, Seam 3). This replaces the informal single-node guideline of D25.
- **Warn, not refuse.** Estimates are approximate, so the check warns rather than refusing. A unit that does exceed its allocation fails as resource exhausted (D31), and memory escalation (S8) may be added later.
- **Spill disk.** DuckDB's temporary directory is placed on the unit's ephemeral volume, with its maximum size set from the unit's allocation, as memory and thread limits are (D25), so that a spilling unit fails cleanly rather than being evicted.
- **Calibration.** Peak memory and spill volume are recorded per task run as time series (CORE 4.2, CORE 4.6) and used to refine estimates; the same measurements serve the cost-informed fusion policy (D33).
- **Later engines.** D25's rule that location, not size, selects the engine held while the only alternative to in-process work was a warehouse, which is a different location. An engine that reads the same files as the in-process engines, such as Spark, can only be chosen by capacity. When one is added, the selection precedence becomes: explicit override, hard constraints (D26), dialect capability and connection policy (D28), data location, then capacity among the engines at that location. The planner records the reason, and plan pinning (D28) protects production workflows from unannounced moves.

*References:* D13 · D23 · D25 · D26 · D28 · D31 · D33 · S8 · CORE 2.4 · CORE 2.26 · CORE 4.2 · CORE 4.6

#### D35 · Ephemeral extraction

**Status:** Decided

No source is copied unless its author chooses to copy it. A read from an external source may be **ephemeral**: performed at run time, with nothing stored unless a downstream output is, and fusable into the transformations that follow. Not every team needs reproducibility, and copying terabytes into the customer's storage because a source is unversionable is not a cost the platform imposes (D36). Added in v0.10.

- **Two independent properties.** How a source read is handled is set by two properties that combine freely:
  - **Storage**, chosen explicitly by the author for every external source: **ephemeral** (read at run time, nothing stored, fusable) or **copied** into a raw managed dataset (D4, D13) with configurable retention. There is no default; the set-up shows the consequences of each choice.
  - **Version**, a property of the source rather than a choice: where the source can identify what was read — an Iceberg snapshot, an object version, an immutable logical interval — the platform records that version on every read, whatever the storage choice.
- **Combinations.** An ephemeral read of a versioned source stays eligible for re-execution and verification for as long as the source retains that version (for example until an Iceberg snapshot expires), and is cacheable. An ephemeral read of an unversioned source caps the run at Traceable (D7): re-executing it as recorded and verifying it are unavailable, leaving only running again on current data (CORE 2.16), and it is not cacheable unless a time-to-live is set (CORE 2.13). A copied read is eligible for re-execution for as long as the copy is retained, whether or not the source is versioned; copying a versioned source protects against the source expiring its versions.
- **Amends.** D4: an unversionable source is no longer copied by default, and reference without copying becomes the ephemeral storage choice, which may be fused. The fusion conditions in the key terms: the output of an external-source read must be stored only when its source is copied. D13: the rule that downstream reruns read the raw partition rather than re-query the source applies to copied sources.
- **Still recorded.** Every read records its provenance, the source version where one exists, and the range of positions consumed where the extraction strategy provides one, so lineage stays complete and incremental cursors work under either storage choice (DE 1.2).
- **Deletes.** Detecting hard deletes by comparing snapshots needs the previous snapshot's keys; for an ephemeral read of an unversioned source this is available only if a compact key set is retained per run.
- **Where copies live.** Under bring-your-own-compute, a copy is written to the customer's own storage target (D4, D22), never to vendor infrastructure; only the fully managed topology stores it with the vendor. The cost an ephemeral read avoids is therefore the customer's own storage.
- **Revised in v0.10.** An earlier draft of this decision presented referenced-by-version, copied and ephemeral as three exclusive modes and left the default open; version and storage are independent, and the storage choice is always explicit.

*References:* D4 · D7 · D13 · D22 · D33 · D36 · CORE 2.13 · CORE 2.14 · CORE 2.16 · DE 1.2 · DE 1.7

#### D36 · Data-engineering practice first, reproducibility by choice

**Status:** Decided

Standard data-engineering practice comes first; reproducibility and the constraints it brings are opt-in. The platform never stops a team from working the way data engineers normally work in order to protect a reproducibility guarantee the team has not asked for. Most organisations do not need reproducibility tiers, and a platform that imposes their costs drives users away. Added in v0.10.

- **Always on.** What costs little and serves ordinary engineering as well: provenance and lineage, recorded read positions and source versions, pinned image digests, and the computed tier, available as information and never blocking.
- **Opt-in.** Anything that costs storage, compute or freedom of practice for the sake of reproducibility: copying sources (D35), protecting inputs from retention beyond what ordinary retention keeps, verification runs, warnings before tier decay, and any rule that refuses a plan, a publication or a design because it would lower a tier.
- **Test.** Every proposed rule is checked: does it constrain a standard practice, or add storage or compute cost, for the sake of reproducibility? If so, it is optional and off unless the team turns it on.
- **Reproducibility setting.** One setting per project, with per-workflow override, turns the opt-in behaviours on together: protection of inputs beyond ordinary retention, warnings before decay, and the verification policy (S2). It is off by default.
- **Retention.** Ordinary retention governs; runs decay to Traceable as their inputs expire (D7). Preserving inputs referenced by provenance beyond retention happens only where the reproducibility setting is on. Protection of the inputs of runs still in progress (D14) is operational and always applies.
- **Decay warnings.** Shown only where the reproducibility setting is on.
- **Guard rails.** Rules that protect correctness rather than reproducibility, such as leakage prevention (DS 2.8) and temporal splits (DS 3.1), are kept as warnings an author can override rather than refusals.
- **Local execution.** The restriction D11 places on publishing from a future local backend is reconsidered under this principle when such a backend is taken up.

*References:* D4 · D7 · D11 · D14 · D23 · D35 · CORE 5.4 · CORE 5.7 · CORE 6.5

#### D37 · Incremental extraction state

**Status:** Decided

Incremental extraction keeps no separate per-task state store. The cursor between runs is the end position recorded by the last successfully committed extraction run, derived from catalogue metadata the platform already writes. Added in v0.10.

- **Change detection.** A strategy declared by each connector, with a declared position type: full snapshot (no position; hard deletes found by comparing snapshots by key), watermark polling (a timestamp range; hard deletes missed), append-only key range, log-based change data capture (a log offset; deletes captured), API sync token (an opaque token; deletes usually captured) or file listing (a set of files; deletions found by comparing listings). The platform shows whether a strategy captures hard deletes and offers periodic full-snapshot reconciliation where it does not (DE 1.3).
- **Cursor.** The end position recorded by the last successfully committed extraction run (D12 Seam 4, CORE 5.9), written in the same catalogue transaction as the commit (D15), so the cursor advances if and only if the data commits. Failed and fenced attempts commit nothing, so retries start from the same position. The record is catalogue metadata: it survives data retention and does not depend on whether the extracted bytes are kept (D35).
- **Frontier.** A per-dataset projection of the furthest committed position, maintained in the same transaction for fast lookup and rebuildable from the position records.
- **Overlap.** Extraction runs on a cursor-based source queue rather than run concurrently (CORE 3.7); single production (D13) already guarantees one writer.
- **Bootstrap.** A first run with no committed position performs a full load and records the position at the snapshot point, such as the log offset at snapshot start (DE 1.4).
- **Resets.** Re-synchronising from scratch or from a given position is a parameter of one run, recorded in its provenance. Re-extracting a past interval produces a new version of that partition and does not rewind the frontier.
- **Clock.** Upper bounds for watermark polling come from the source's clock, not the platform's.
- **Within a run.** Resuming a partially completed extraction uses the checkpoint slot (D31), not the cursor.
- **Deletes.** Snapshot-comparison strategies retain a compact key set per run, so detection survives short retention and ephemeral reads.
- **Incremental transforms.** A node that maintains its output incrementally reads the previous version of its own output as an input, through a "latest" partition dependency (D13), resolved and recorded under D14; it needs no state store either.
- **Comparison.** Dataiku DSS has no first-class cursor; incremental loads there are built from time-based partitions or from the maximum timestamp of the target passed as a variable.

*References:* D12 · D13 · D14 · D15 · D31 · D35 · CORE 3.7 · CORE 5.9 · DE 1.2 · DE 1.3 · DE 1.4 · DE 1.5

#### D38 · Point-in-time retrieval

**Status:** Decided

Point-in-time retrieval (MLE 1.2) needs no change to the dataset model. Event time is carried by event-time metadata on datasets (D12 Seam 6). Knowledge time — when the platform learned of a value — comes from a dataset's publication history, since every snapshot has a commit time (D15), or from a row-level ingestion timestamp written at extraction, which is standard practice. Added in v0.10.

- **Point-in-time join.** A palette node matches each label to the feature values whose event time and knowledge time both precede the label time.
- **Limit.** As-of accuracy at version level reaches back only as far as retained snapshot history (D36); a row-level ingestion timestamp avoids that limit.

*References:* D12 · D13 · D15 · D35 · D36 · MLE 1.2 · MLE 5.3

#### D39 · Online model serving

**Status:** Decided

Low-latency online model endpoints are out of scope. Models are served by external serving systems; the platform covers packaging for deployment (MLE 3.5), batch and scheduled scoring (MLE 4.1), and the registry, lineage and approvals around them. Added in v0.10.

*References:* D6 · D12 · MLE 3.5 · MLE 4.1 · MLE 4.2

---

## Open items

Questions the current design anticipates but has not yet resolved. Each item is carried forward for discussion and will become a decision or a catalog line once settled. Items marked as shaping the core should be settled before the corresponding part of the model is implemented.

### Behaviour at scale

#### S1 · Retention cost of reproducibility

**Status:** Open

Retaining inputs so that runs remain re-executable is expensive. The mitigation is to reference rather than copy: an Iceberg snapshot identifier or an S3 object version costs nothing to record, whereas a materialised copy incurs storage cost indefinitely. Tier decay (D7) is therefore a statement about the point at which retention ceased to be funded.

- **To settle.** Default retention periods, guidance on when an author should copy a source rather than read it ephemerally (D35), and which budget carries the cost.

*References:* D7 · CORE 5.2 · CORE 6.5

#### S2 · Verification cost at scale

**Status:** Open

A verification run consumes as much compute as the original run. At scale, verification must be sampled or tiered: compare summary statistics first — row counts, per-column aggregates, key hashes — and perform a full comparison only on request.

- **To settle.** The default verification level, the policy for selecting which runs are verified, and how a partial verdict is represented.

*References:* CORE 5.7 · CORE 5.8

#### S3 · Preview and inspection generation

**Status:** Open

Previews and node-level inspection data must be sampled and generated at write time. Computing them on demand over a large artifact makes the interface unusable and the cost unpredictable.

- **To settle.** Sample sizes and sampling method per artifact type, and the retention period for preview data.

*References:* CORE 6.3 · CORE 6.6

#### S4 · Scheduler load under large fan-out

**Status:** Open

Large fan-out places load on the control plane rather than the data path: 10,000 task runs means 10,000 state records and lease renewals. Batched state transitions, leases and fair queuing are the mechanisms that absorb this.

- **To settle.** The target fan-out the scheduler must sustain, the batching strategy for state writes, and lease renewal intervals. Also whether task runs under large maps are created up front or in batches (D31).

*References:* CORE 2.3 · CORE 2.11 · CORE 3.6

#### S5 · Metadata and log growth

**Status:** Open

Task run tables and log volumes grow without bound. Both require partitioning and archiving, and logs must remain outside the metadata database.

- **To settle.** Archival thresholds and destinations, retention periods per data class, and the query paths that must remain fast against archived history.

*References:* CORE 4.1 · CORE 4.3

#### S6 · Data locality and egress

**Status:** Open · deferred (D26)

Execution units should be scheduled in the region and availability zone where their data resides. Cross-region reads are slow and, in cloud deployments, chargeable.

- **Deferred.** Placement constraints are deferred from the first release. Location recording, eligibility checks on cache hits and explicit placement by the planner are kept so that they can be introduced without rework (D26).
- **To settle.** Whether placement constraints are first-class in the IR or supplied by the backend abstraction, and how a conflict between placement and available capacity is resolved.

*References:* D26 · CORE 2.9 · CORE 2.4

#### S7 · Skew and stragglers

**Status:** Open

A single partition an order of magnitude larger than its peers determines the runtime of an entire stage. Per-shard timing and the option to rebalance must be visible to the user.

- **To settle.** Whether rebalancing is automatic or advisory, and what skew diagnostics are surfaced on the canvas and in run history.

*References:* CORE 2.3 · CORE 4.2 · CORE 4.6

#### S8 · Out-of-memory escalation

**Status:** Open

When an execution unit is terminated for exceeding its memory allocation, retrying once at a higher memory tier and recording the escalation is preferable to failing the run outright.

- **To settle.** The escalation ladder and its ceiling, whether escalation is enabled by default, and how the escalation is reflected in cost attribution and in the run record.

*References:* CORE 2.5 · CORE 2.4 · CORE 4.5

### Data lifecycle · to settle before the model hardens

#### S9 · Version selection and consistent read sets

**Status:** Resolved · D14

Which version of an input a run reads — the latest at the moment a node starts, the latest when the run starts, or a pinned version — and whether a run reading several datasets sees them all as of the same instant. Without snapshot isolation across inputs, a run can join one day's customers to another day's orders.

- **Outcome.** Versions resolved once at run start under snapshot isolation; pinning per input; coherent reads declared by the user. See D14.

*References:* CORE 5.2 · CORE 5.9 · D7

#### S10 · Atomic publication

**Status:** Resolved · D15

A run that writes several partitions and fails part-way must not leave a partially published version visible, and a retried attempt must never publish twice. This implies staged writes followed by a single commit.

- **Outcome.** Stage, then commit once. The metadata catalog is the commit point for managed datasets; external targets use their own transactions or report partial publication; publication groups are declared by the author. See D15.

*References:* CORE 6.8 · CORE 6.9 · CORE 2.5

#### S11 · Consumer policy for stale or failed inputs

**Status:** Resolved · D16

When an upstream dataset is stale or its latest publication failed, a consumer may wait, skip its run, or proceed with a warning. Without a declared policy, one late source either silently stalls or silently degrades everything downstream.

- **Outcome.** Per-input policies (wait, proceed, skip, fail, optional) with configurable defaults; degraded outputs cascade downstream with their originating reason. See D16.

*References:* DE 4.2 · DE 4.4 · CORE 3.5

#### S12 · Non-tabular datasets

**Status:** Resolved · D17

Files such as BAM and FASTQ, trained models and feature sets must follow the same lifecycle. For these, schema becomes a format plus metadata, a partition is typically a sample or entity, and comparators and previews differ.

- **Outcome.** Families and first-release scope recorded in D17, with the structural capabilities they require.
- **Outcome.** Models are a specialised dataset type (D17).
- **Outcome.** One extension point per family, running in the data plane, internal in the first release (D17).

*References:* CORE 5.8 · CORE 6.3 · MLE 3.2

#### S13 · Stable identity under rename

**Status:** Resolved · D19

A dataset needs an immutable internal identifier separate from its mutable name, so that renaming it does not break lineage, consumers or history.

- **Outcome.** Fixed names with display titles and an immutable internal identifier; deleted names are not reused (D19).

*References:* CORE 6.1 · CORE 1.6

#### S14 · Backfill commit granularity

**Status:** Resolved · D20

A backfill over 31 days may publish 31 snapshots or one. Per-interval commits enlarge version history and trigger repeated downstream reconciliation; a single commit delays all results until the final interval completes.

- **Outcome.** Per-interval commits with coalesced downstream reconciliation; atomic mode for restatements; lower priority than scheduled runs (D20).

*References:* CORE 3.4 · CORE 6.9 · D13

### Data lifecycle · may be settled later

#### S15 · Retention defaults and legal holds

**Status:** Open

Default retention per layer, legal holds that suspend deletion, and exemption of pinned versions from garbage collection.

- **To settle.** Per-layer defaults and who may place or lift a hold. Also the default retention of quarantined versions (D31).

*References:* S1 · CORE 6.5

#### S16 · Deprecation and deletion

**Status:** Open

A deprecation notice period, notification of consumers, and blocking of deletion while active consumers remain.

- **To settle.** Notice periods and the override path for urgent deletion.

*References:* CORE 6.1 · CORE 6.10

#### S17 · Breaking schema changes

**Status:** Open

Whether a breaking change rewrites history or publishes a parallel major version of the dataset while consumers migrate.

- **To settle.** The default strategy and how long parallel versions are maintained.

*References:* DE 2.6 · DE 5.8

#### S18 · Overriding a failed quality gate

**Status:** Open

Who may release a quarantined version into use, under what conditions, and with what audit trail.

- **To settle.** Required roles and whether an override expires. The override mechanics are recorded in D31.

*References:* DE 4.4 · CORE 7.4

#### S19 · Access control and visibility

**Status:** Open

Whether a user without read access to a dataset may still see that it exists, and see it in lineage.

- **To settle.** Visibility rules for catalog entries, lineage nodes and previews. The default is recorded in D30: unreadable entities are hidden.

*References:* CORE 7.1 · DE 5.4

#### S20 · Sharing across projects and tenants

**Status:** Open

Read-only sharing of a dataset with another project and, in the cloud edition, with another tenant.

- **To settle.** The sharing model, its interaction with cache scope (D9), and revocation.

*References:* D5 · D9

#### S21 · Lineage interoperability

**Status:** Open

Export of lineage in the OpenLineage format so that external catalogs such as DataHub, Unity Catalog or Glue can consume it.

- **To settle.** Export only, or import as well, and at what granularity.

*References:* CORE 5.3 · DE 5.1

#### S22 · Cost attribution per dataset

**Status:** Open

Attribution of storage and of the compute that produces a dataset, to support decisions about retention and refresh frequency.

- **To settle.** The attribution method for shared upstream work.

*References:* CORE 4.5

#### S23 · Data residency

**Status:** Open · deferred (D26)

A declared region on a dataset, constraining where it is stored and where the units that read it may run.

- **Deferred.** Residency rules are deferred with placement constraints (D26). Because every attempt and artifact records its location from the first release, data stored and processed before enforcement can still be judged against a residency rule introduced later.
- **To settle.** Enforcement at storage, at placement, or both.

*References:* S6 · D26 · CORE 7.3

### Authoring and execution

#### S24 · Dynamic output schemas

**Status:** Open

Nodes whose output columns depend on the data — a pivot or one-hot encoding over values not known in advance — break design-time schema propagation through the IR, on which validation, the canvas, contracts and column-level lineage all rely.

- **To settle.** Whether such nodes must declare their output columns in advance, may be marked as resolved at run time with downstream schemas shown as pending until a first run, or both; and how validation, contracts and column-level lineage treat a schema known only after execution.

*References:* D10 · D25 · CORE 1.2 · DE 5.8

---

## Capabilities

Capability statements by section. Flags: `[shapes the core]` imposes a requirement on the scheduler or domain model and is expensive to retrofit; `[cross-discipline]` is demanded from more than one direction; `[deferred]` has been pushed out of the initial scope by a decision; `[new in v0.x]` records the revision that added the line.

### Core platform (CORE) — 103 capabilities

The substrate all three disciplines run on. Everything here is discipline-agnostic by construction — if an item only ever serves one discipline, it has been filed under that discipline instead.

#### 1 · Authoring

*Constructing and evolving a pipeline definition.*

- **CORE 1.1** — Assemble a pipeline on a canvas as a graph of typed nodes with declared inputs and outputs.
- **CORE 1.2** — Validate a graph before it runs: cycles, unbound parameters, incompatible port types, missing credentials, unsatisfiable resource requests.
  - *Note:* Validation at author time, rather than failure part-way through a run, largely determines the perceived quality of the builder.
- **CORE 1.3** — Parameterise a workflow and supply values per run, with typed defaults and validation.
- **CORE 1.4** — Nest a workflow as a single node inside another workflow. `[shapes the core]`
  - *Note:* Composition keeps a visual graph legible beyond roughly 30 nodes. A referenced workflow is inlined into the parent run, pinned to a version, with each task run recording its origin (D31). Composition does not determine fusion (D33).
- **CORE 1.5** — Version a workflow definition, diff two versions visually, and roll back.
- **CORE 1.6** — Round-trip between the visual graph and a text definition that can be committed to git. `[shapes the core]`
  - *Note:* Required by the engineering audience. Round-trip fidelity, rather than one-way export, is the meaningful capability, and it constrains the IR design substantially.
- **CORE 1.7** — Publish, share, fork, and re-run a workflow template from a catalog.
- **CORE 1.8** — Drop in a custom code node — Python, SQL, or shell — with its own dependency spec.
  - *Note:* The required escape hatch: visual tools without one are abandoned at the first unsupported operation. Code nodes are offered as SQL and Ibis, both eligible for pushdown (D27), Polars and pandas, in-process, and container commands for command-line tools, all on equal terms (D25).
- **CORE 1.9** — Register a third-party plugin node: declared interface, container image, parameter schema, UI form.
  - *Note:* Node ports declare data types, never format plugins, so a node works with any dataset of the declared type. Connectors to source and target systems are node plugins (D18).
- **CORE 1.10** — Declare a node's dependencies as packages and let the platform build, cache and pin the container image, instead of writing Dockerfiles. `[new in v0.3]`
  - *Note:* Prebuilt base images for Python, R and common scientific tools keep builds fast. The resolved lockfile and resulting image digest become part of the run record (D11). Builds and the registry may run in the customer's environment (D22).
- **CORE 1.11** — Declare the execution modes a node type supports, and refuse a graph that uses a node in a mode it does not implement. `[new in v0.5]`
  - *Note:* Every node type declares `[batch]` in the initial scope (D12, Seam 3).
- **CORE 1.12** — Define each built-in node once, as an Ibis expression — eligible for pushdown to a warehouse unless it relies on in-process functions — or in Polars by justified exception, and conformance-test every Ibis node against DuckDB and each supported warehouse dialect. `[shapes the core]` `[new in v0.8]`
  - *Note:* One implementation per node; a node that cannot be compiled for a dialect declares the dialects it supports. Moving a node between Ibis and Polars is a new node version (D25). Revised in v0.9: pushable nodes are Ibis expressions rather than portable SQL text (D27). Revised in v0.10: every built-in node is Ibis first, through four tiers, and Polars implementations are justified exceptions (D27).

#### 2 · Execution

*Turning a definition into running work.*

- **CORE 2.1** — Execute a workflow and observe per-task state transitions in real time.
- **CORE 2.2** — Run independent branches concurrently, bounded by workflow, project, and cluster limits.
- **CORE 2.3** — Fan a node out over a collection and gather the results back into one downstream input. `[shapes the core]` `[cross-discipline]`
  - *Note:* Scatter/gather over 10,000 items is routine for sequencing workloads and parameter sweeps, and it determines how task state is stored and how the run aggregate is sized.
- **CORE 2.4** — Declare per-task resources: CPU, memory, GPU, ephemeral disk, wall-clock timeout.
  - *Note:* Ephemeral disk includes DuckDB's spill space. Per-backend ceilings bound every request, and the planner checks estimated working sets against them (D34).
- **CORE 2.5** — Define retry policy per task, distinguishing retriable infrastructure failure from terminal task failure.
  - *Note:* Commits carry the attempt identity as a fencing token, so a superseded attempt cannot publish after its retry (D15). Each failed attempt records a failure class; infrastructure failures draw on a platform retry budget separate from the author's policy, and a fenced attempt is not a failure (D31).
- **CORE 2.6** — Skip re-execution when a task's inputs, parameters, code, and image are unchanged. `[shapes the core]` `[cross-discipline]`
  - *Note:* Highest-value feature for iterative work: change one parameter and only that node and its descendants rerun. Also provides resume-after-failure (CORE 2.7) and shared prefixes in sweeps for free. Keys are hybrid: input-addressed for every node, chained through nodes rather than units, plus content-addressed early cutoff for small artifacts (D8). Reuse is within a project by default, across projects of a tenant by opt-in, and never across tenants (D9). Verification runs always bypass the cache.
- **CORE 2.7** — Resume a failed run from the point of failure, and re-run a single node together with its descendants.
- **CORE 2.8** — Pause, resume, and cancel a run, with graceful drain of in-flight tasks.
  - *Note:* Pausing stops dispatch and lets running attempts finish, after which the run is suspended; cancelling signals running attempts at their next heartbeat (D31).
- **CORE 2.9** — Target a different execution backend per run or per task — local container, Kubernetes, HPC scheduler, cloud batch. `[shapes the core]`
  - *Note:* Decided (D3): the custom IR compiles down to backends. This is the anti-corruption layer; each backend reports failure, resource limits, and cancellation differently, and all of it must be normalised into one vocabulary.
- **CORE 2.10** — Branch conditionally, skip a subgraph, and iterate until a condition holds. `[shapes the core]`
  - *Note:* Decided (D2): workflows are control-flow graphs, not strict DAGs. Only structured constructs are permitted, and iterations unroll into an acyclic run trace (D2).
- **CORE 2.11** — Survive infrastructure loss: a run continues correctly after a scheduler restart or a worker node disappearing. `[shapes the core]`
  - *Note:* Implies leases with heartbeats and a reconciliation loop rather than fire-and-forget event handling.
- **CORE 2.12** — Declare that a node has external side effects — writes to an outside system, sends a message, triggers a deployment — so it is never served from cache and is suppressed or redirected during verification runs. `[shapes the core]` `[new in v0.2]`
  - *Note:* Without this, a cached "load to warehouse" silently never reloads, and a verification run re-sends the email.
- **CORE 2.13** — Control caching directly: force-rerun a node and its descendants, disable caching per node or per run, set a time-to-live on nodes reading external sources, and pin a cache boundary inside a fused chain or mark a node to run as its own unit. `[new in v0.2]`
  - *Note:* Every skipped node indicates the earlier run its output came from, so that a cached result is not mistaken for a fresh one; it is recorded as a task run with the outcome reused (D31). Revised in v0.10: marking a node to run as its own unit added (D33).
- **CORE 2.14** — Fuse adjacent nodes into a single execution unit automatically, and show on the canvas which nodes share a unit. `[shapes the core]` `[new in v0.3]`
  - *Note:* Fusion only groups nodes with the same image, execution location and compatible resources, and never across control flow, published datasets, outputs used by several units, pinned cache boundaries, reads from copied external sources, side-effect nodes, or where it would create a cycle between units. Revised in v0.10: fusion is fully automatic behind a replaceable policy, users can only split, and composites play no part in it (D32, D33).
- **CORE 2.15** — Run an entire workflow locally in a single process, without containers, for development and small data. `[deferred]`
  - *Note:* Deferred (D11). A local worker or a standalone installation may be added later behind the existing backend interface; such runs would be capped at Traceable, or Re-executable with a recorded lockfile, and barred from publishing to datasets with an enforced contract.
- **CORE 2.16** — Offer two distinct rerun actions: re-execute a run exactly as recorded, reading its originally resolved input versions, or run it again on current data. `[new in v0.7]`
  - *Note:* Conflating the two is a common source of confusion about why a rerun produced different results (D14).
- **CORE 2.17** — Install and run the complete platform on a single machine through a container-based deployment, for evaluation, development and small teams. `[new in v0.7]`
  - *Note:* The entry point in the absence of a container-free mode (D11). Execution is driven by the same pull-based agent as in every other deployment (D29).
- **CORE 2.18** — Run execution agents inside a customer's own cloud account or HPC cluster that connect outward to a hosted control plane, pull work and execute it locally. `[shapes the core]` `[new in v0.7]`
  - *Note:* No inbound connectivity into the customer's network is required; only metadata and events cross the boundary (D22). The same agent serves HPC backends, and is used in self-hosted and single-machine deployments too (D29).
- **CORE 2.19** — Choose where each unit runs from where its data lives: push relational nodes down to the warehouse holding their inputs, process files and uploads in-process, process inputs held in different locations in-process after reducing each warehouse's share by pushdown, never moving data into a warehouse, and show the engine, location and reason for every unit before the run. `[shapes the core]` `[new in v0.8]`
  - *Note:* Precedence: explicit override, hard constraints (deferred, D26), dialect capability, data location. Size does not select the engine; extraction beyond a configurable cap asks the author rather than proceeding, and the plan suggests storing data in the warehouse where that would allow pushdown (D25). Once an engine shares a location with the in-process engines, capacity chooses between them (D34).
- **CORE 2.20** — Run DuckDB and Polars nodes together in one execution unit, chaining consecutive nodes on the same engine into a single segment and handing data between engines as Arrow. `[new in v0.8]`
  - *Note:* Each engine's optimiser sees a whole segment; memory and thread limits for both engines derive from the unit's allocation. Non-tabular nodes run in Python or container-command runtimes and scale by fan-out (D25).
- **CORE 2.21** — Record the backend and region of every attempt, and a storage location identifying the region of every artifact, from the first release. `[shapes the core]` `[new in v0.9]`
  - *Note:* Required before placement and residency constraints exist, because locations cannot be reconstructed for historical runs and artifacts (D26).
- **CORE 2.22** — Constrain where units run through hard placement requirements, such as region, residency or remaining inside a warehouse, and soft preferences, and reject plans whose hard constraints cannot be met. `[deferred]`
  - *Note:* Deferred (D26). The location record (CORE 2.21), eligibility checks on cache hits and explicit placement in the plan are kept so that this can be added without rework.
- **CORE 2.23** — Set a policy on each warehouse connection: whether the platform may compute in the warehouse, which compute cluster it uses and at what size, and an optional credit budget; treat a connection without compute rights as unavailable for pushdown. `[shapes the core]` `[new in v0.9]`
  - *Note:* Set by the warehouse's owner rather than by workflow authors; the planner places units automatically within it (D28).
- **CORE 2.24** — Pin the plan of a production workflow, so that a change in where its units run is reported rather than applied. `[new in v0.9]`
  - *Note:* A run whose pinned placement can no longer be honoured stops before execution until the author accepts a new plan (D28).
- **CORE 2.25** — Operate entirely on customer-provided compute: a container-capable backend for execution units and the customer's warehouse for pushdown, with the vendor hosting only the interface and control planes. `[shapes the core]` `[new in v0.9]`
  - *Note:* Bring-your-own-compute is the primary deployment model (D22). A warehouse alone runs only pushdown work; every other node needs the container backend.
- **CORE 2.26** — Insert a repartition step when a node groups by a key other than its input's partitioning: rewrite the data hash-bucketed by that key, then fan the node out per bucket. `[shapes the core]` `[new in v0.9]`
  - *Note:* Lets in-process engines scale partition-local work by any key without a distributed engine. Work that no key can divide remains flagged by the capacity check (D34).

#### 3 · Scheduling & triggering

*Deciding when work happens and for which slice of time.*

- **CORE 3.1** — Schedule a workflow on a cron or interval, with timezone and DST handling.
- **CORE 3.2** — Trigger on an event: webhook, file arrival, dataset update, upstream workflow completion.
- **CORE 3.3** — Treat a run as covering a logical interval, not merely a wall-clock moment. `[shapes the core]`
  - *Note:* "The run for 2026-09-19" must be reproducible tomorrow. Without this, backfills and partition reruns are not expressible at all.
- **CORE 3.4** — Backfill a historical date range with bounded concurrency and per-interval status. `[shapes the core]`
  - *Note:* Intervals commit as they complete; commits carry the backfill identifier and run below scheduled work in priority (D20).
- **CORE 3.5** — Express a dependency from one workflow onto another workflow's output, where neither owns the other. `[shapes the core]`
- **CORE 3.6** — Share capacity fairly: one project's large fan-out must not starve every other tenant. `[shapes the core]`
  - *Note:* Fairness is a scheduler property, not a limit setting. Retrofitting it into FIFO dispatch means rewriting the scheduler.
- **CORE 3.7** — Constrain overlap: prevent or queue a second run of the same workflow while one is in flight.
- **CORE 3.9** — Declare how a node's output partitions depend on its input partitions — identity, a time window, all available, the latest, or specific values — or let a merge node discover the affected partitions from the data at run time. `[shapes the core]` `[new in v0.7]`
  - *Note:* Required wherever one input partition affects several output partitions, such as late-arriving records or rolling windows. Declared mappings let the plan be known in advance; discovered mappings do the minimum work but decide the plan as the run proceeds (D13).
- **CORE 3.10** — Validate that a schedule's logical interval is compatible with the partitioning of the datasets it writes, including timezone, and require an explicit open-partition declaration when runs are finer-grained than partitions. `[new in v0.7]`
  - *Note:* Open partitions are appended to by successive runs and become visible as complete only when marked so. Misaligned boundaries are rejected rather than adjusted (D13).
- **CORE 3.11** — Declare, per input, whether a run waits for it, proceeds on its last valid version, skips the interval or fails when the input is stale, failed or missing, and mark inputs as optional where the output can be produced without them. `[shapes the core]` `[new in v0.7]`
  - *Note:* Defaults: scheduled runs wait with a timeout derived from the output's freshness expectation, then fail and alert; manual runs proceed on the last valid version with a warning. Waiting holds no compute, and input versions are resolved after the wait (D16).
- **CORE 3.12** — Defer downstream reconciliation while a backfill runs and plan it once over all changed partitions, at completion or at batch boundaries. `[new in v0.7]`
  - *Note:* Prevents each downstream partition being rebuilt once per upstream commit inside its lateness window (D20).
- **CORE 3.13** — Declare a backfill as an atomic restatement, staging every interval and committing a single snapshot at the end. `[new in v0.7]`
  - *Note:* Ensures consumers never read a mixture of partitions computed under old and new logic (D20).
- **CORE 3.14** — Request that a dataset be made current through a given time, and have the platform plan and run the minimum work across the project's workflows, with every resulting run grouped under the request that caused it. `[shapes the core]` `[new in v0.7]`
  - *Note:* Build modes: only this dataset, upstream where modified, all upstream, downstream (D24).
- **CORE 3.15** — Declare a freshness policy on a dataset and have the reconciler keep it satisfied automatically, in place of a schedule; and make materialisation requests across project boundaries. `[deferred]`
  - *Note:* Deferred (D24).

#### 4 · Observability

*Seeing what happened, while it happens and afterwards.*

- **CORE 4.1** — Tail a task's logs live, and retrieve them from durable storage after the run, with search.
  - *Note:* Two systems behind one interface: a streaming path and an archive path. Logs must not be stored in the metadata database.
- **CORE 4.2** — See CPU, memory, GPU, and I/O usage over the life of each task, against what it requested.
  - *Note:* Peak memory and spill volume also calibrate the planner's capacity estimates (D34).
- **CORE 4.3** — Review run history as a timeline, including queue time versus run time and the critical path.
- **CORE 4.4** — Alert on failure, on SLA breach, and on custom conditions, to email, chat, or webhook.
- **CORE 4.5** — Attribute compute cost to a run, workflow, project, and user.
- **CORE 4.6** — Retain task metrics as time series over the life of a task rather than as end-of-run summaries. `[new in v0.5]`
  - *Note:* Supports straggler and skew analysis now, and lag, watermark skew and backpressure without schema change later (D12, Seam 10).
- **CORE 4.7** — Keep logs and metrics within the customer's environment in hybrid deployments, with live tailing proxied through the execution agent. `[new in v0.7]`
- **CORE 4.8** — Tag every query the platform runs in a warehouse, and every job it runs on a customer backend, with the platform, workflow and run, and report usage per workflow. `[new in v0.9]`
  - *Note:* Makes spend caused by the platform visible in the customer's own query history and infrastructure accounting (D22, D28, S22).

#### 5 · Reproducibility & provenance

*The stated contribution of the project. Everything here is a claim the system has to be able to defend.*

- **CORE 5.1** — Pin every task to an immutable image digest, never a mutable tag, and record the platform and node versions used.
- **CORE 5.2** — Record for every task run: input dataset versions, parameter values, environment, random seeds, and the resolved code revision.
- **CORE 5.3** — Trace any output artifact backwards to every input, task, and parameter that produced it, and forwards to everything derived from it. `[cross-discipline]`
- **CORE 5.4** — Report the reproducibility tier a given run actually achieves, and what stops it reaching the next one. `[shapes the core]`
  - *Note:* Bit-identical output is not a goal (D7). Tiers (D7): Traceable → Re-executable → Reproducible. Undeclared external inputs, runtime installs, unseeded randomness and unordered parallel output each cap the tier. Exposing this as a visible, first-class property is the principal technical differentiator identified to date.
- **CORE 5.5** — Re-execute a historical run exactly as it originally ran, including its original definition version.
- **CORE 5.6** — Export a run as a portable bundle — definition, pinned images, input references, provenance — that a third party can execute elsewhere.
  - *Note:* Supports the portability objective, and requires the IR to be self-contained rather than dependent on platform-internal state.
- **CORE 5.7** — Run a verification rerun of a recorded run and compare its outputs to the original using a comparator for each artifact type — tables ignoring row order with float tolerance, models by predictions on a probe set, metrics within a tolerance. `[shapes the core]` `[new in v0.2]`
  - *Note:* The only way to establish the Reproducible tier. Comparators are a plugin point. Verification costs as much as the original run, so it needs a policy: on demand, sampled, or for runs a user marks as important.
- **CORE 5.8** — Register comparators and canonicalisers per artifact type through the plugin mechanism, with configurable default tolerances that are recorded alongside every verdict. `[new in v0.3]`
  - *Note:* Built-ins cover tables, metrics, JSON, text and common model types; domain plugins ship their own (e.g. BAM, VCF). Comparison is layered for large artifacts — byte hash, then summary statistics, then full comparison — and the verdict records which level was reached.
- **CORE 5.9** — Record the range of positions consumed from every source — a snapshot identifier, object version or timestamp range — rather than only the identity of the input. `[shapes the core]` `[new in v0.5]`
  - *Note:* Required by incremental extraction (DE 1.2) and by partition-level rerun; the same record generalises to offset and window lineage if streaming is added (D12, Seam 4).
- **CORE 5.10** — Resolve and record the versions of all inputs once at run start, read them under snapshot isolation for the whole run, and allow any input to be pinned to a specific version. `[shapes the core]` `[new in v0.7]`
  - *Note:* Every node in a run sees the same input versions regardless of when it starts (D14).
- **CORE 5.11** — Declare coherent reads for a workflow, with per-input override, so that inputs are resolved to versions consistent along lineage. `[new in v0.7]`
  - *Note:* Prevents joining a derived dataset with a newer version of its own upstream. Where no coherent set exists, the run fails with an explanation or follows its stale-input policy (D14, D16).

#### 6 · Data & artifacts

*What flows between tasks, and what outlives the run that made it.*

- **CORE 6.1** — Treat a dataset as a first-class object with its own identity, versions, partitions, schema, and owner — independent of the run that produced it. `[shapes the core]` `[cross-discipline]`
  - *Note:* Decided (D4). The single decision that unifies the three disciplines: an ML feature table, an ETL output table, and a genomic alignment file become the same concept. Without it, freshness, data-triggered scheduling, and cross-workflow dependency are all inexpressible.
- **CORE 6.2** — Store artifacts at identity-addressed paths with pluggable object-store backends, each described by a catalog manifest listing its files, byte digests, roles, schema, statistics and, where applicable, a canonical content hash.
  - *Note:* Revised in v0.7: paths are not content-addressed, which would force a second write of large outputs. Deduplication by digest is optional and asynchronous (D23). Byte and row counts per partition are mandatory statistics (D34).
- **CORE 6.3** — Preview an artifact in the browser — table, chart, image, model summary — without downloading it.
  - *Note:* Previews of large artifacts must be generated at write time rather than on demand, otherwise the interface stalls on multi-gigabyte outputs.
- **CORE 6.4** — Derive lineage from declared reads and writes rather than requiring the user to document it. `[cross-discipline]`
- **CORE 6.5** — Apply retention and garbage-collection policies to intermediates, preserving inputs referenced by provenance beyond ordinary retention where the reproducibility setting is on.
  - *Note:* Versions resolved by a run still in progress are protected until it finishes (D14). Retention is also reproducibility policy: a run drops to Traceable when its inputs are collected (D7). Revised in v0.10: ordinary retention governs; preserving inputs referenced by provenance beyond it, and warning before decay with an offer to pin inputs, happen only where the reproducibility setting is on (D36).
- **CORE 6.6** — Inspect any node inside a fused execution unit: per-node row counts, schema changes and timings; column profiles; traced row samples that follow the same entities through every node; fitted parameters; and full regeneration of an intermediate on demand. `[new in v0.3]`
  - *Note:* Defaults to statistics plus samples; retention is configurable per unit. Sample runs during development execute unfused with every intermediate kept. When a fused node fails, a bounded snapshot of its input is kept. Samples and snapshots are real data and follow the same access control and masking as their source datasets.
- **CORE 6.7** — Represent a dataset as an append-only sequence of positions, of which a point-in-time snapshot is one case. `[shapes the core]` `[new in v0.5]`
  - *Note:* Keeps partitioned and continuously appended datasets under one model, and admits a retained topic later without redefining dataset versioning (D12, Seam 5).
- **CORE 6.8** — Bind a node output to a dataset once, so that every subsequent run publishes a new version automatically; gate publication behind a quality check or approval where required; and promote an existing artifact into a dataset after the fact. `[new in v0.6]`
  - *Note:* Publication is declared, not performed per run. Outputs that are not bound remain run-scoped artifacts, subject to retention and absent from the catalog.
- **CORE 6.9** — Declare a dataset's partitioning scheme, and maintain version history per partition so that a publication creates a snapshot which reuses the partition versions it did not write. `[shapes the core]` `[new in v0.6]`
  - *Note:* Partitions and versions are independent: a partition is a slice of the key space, a version is state over time. Every successful publication produces a version, including routine incremental runs with no structural change. A rerun producing identical content may be recorded as a no-op where a content hash is available (D8).
- **CORE 6.10** — Enforce a single producer per dataset: exactly one node in one workflow may publish to it, while any number may consume it. `[new in v0.7]`
  - *Note:* Prevents racing publications, ambiguous lineage and unclear contract ownership. Multiple sources are combined by one node (D13).
- **CORE 6.11** — Propose a partitioning scheme when a dataset is created, advise on granularity from observed partition sizes, and perform a change of partitioning scheme only as an explicit, owner-initiated migration that revalidates downstream dependency mappings. `[new in v0.7]`
  - *Note:* Granularity is the owner's decision; the platform's suggestions are advisory. Physical layout — file sizing, compaction, clustering — is decided by the platform and does not alter the logical model (D13).
- **CORE 6.12** — Publish by staging new data in an attempt-scoped location and making it current with a single atomic commit, recorded in the metadata catalog for managed datasets and by the target's own transaction for external ones. `[shapes the core]` `[new in v0.7]`
  - *Note:* Readers resolve data through the catalog, so unfinished writes are invisible. Targets that cannot commit several partitions atomically are reported as partially published rather than concealed (D15).
- **CORE 6.13** — Declare a publication group so that several managed datasets written by one node are committed together or not at all. `[new in v0.7]`
  - *Note:* Independent commits remain the default (D15).
- **CORE 6.14** — Mark outputs built on stale, failed or absent inputs as degraded, state the reason, and cascade the marking to every downstream dataset together with its originating cause. `[new in v0.7]`
  - *Note:* A consumer several steps away sees the root cause rather than only its immediate input. The marking clears when the output is rebuilt from ready inputs (D16).
- **CORE 6.15** — Support datasets from six families in the first release — tabular, semi-structured and records, text and documents, images, genomics and life sciences, and ML artifacts — and accept further families through the plugin interface. `[shapes the core]` `[new in v0.7]`
  - *Note:* Formats are handled by family rather than individually; format-specific validation sits within each family (D17). The first development slice supports the tabular family only (D29).
- **CORE 6.16** — Represent one logical file as a group of physical files with declared roles — primary, index, sidecar — that are versioned, moved, retained and deleted together. `[shapes the core]` `[new in v0.7]`
  - *Note:* A BAM requires its index, a VCF its tabix index, a Shapefile several companion files, and some models and arrays are whole directories (D17).
- **CORE 6.17** — Declare linked items within a dataset — paired-end reads, an image and its annotation — and fail validation when one member of a link is missing. `[new in v0.7]`
- **CORE 6.18** — Store collections of many small items as shards with a per-item index, while keeping each item individually addressable for preview, lineage and sampling. `[new in v0.7]`
  - *Note:* Millions of individually stored objects strain storage and metadata alike (S5).
- **CORE 6.19** — Declare whether a dataset's format can be read in ranges, and use that declaration when planning fan-out. `[new in v0.7]`
  - *Note:* Parquet and indexed BAM can be split within a file; gzip-compressed CSV and FASTQ cannot, and must be processed file by file.
- **CORE 6.20** — Define each data format as a platform-owned type with a contract schema, a reader protocol and a conformance suite, and accept plugins that implement a type only when they pass its suite. `[shapes the core]` `[new in v0.7]`
  - *Note:* A plugin declares a manifest — identity, implemented type, runtime image, file-group layout, links and capabilities — and implements required `validate` and `metadata` functions plus optional ones. It never touches the catalog, storage or interface directly (D18).
- **CORE 6.21** — Bind each dataset to exactly one format implementation at a pinned version, record the binding on every dataset version, and change it only through an explicit migration that revalidates the dataset. `[shapes the core]` `[new in v0.7]`
  - *Note:* Upgrades are offered as a bulk action that reports datasets whose validation outcome would change before committing (D18).
- **CORE 6.22** — Let administrators set the allowed format implementations per type at organisation or project level, defaulting to one, so that new datasets bind automatically without users having to choose. `[new in v0.7]`
- **CORE 6.23** — Store managed datasets on platform storage or on customer storage — object storage in the customer's account, a table in their lakehouse catalog, or a table in their warehouse — with targets set at tenant, project or dataset level. `[shapes the core]` `[new in v0.7]`
  - *Note:* Managed describes who owns the lifecycle, not where the bytes sit. Publishing into a customer's lakehouse makes outputs directly usable by their existing tools (D4).
- **CORE 6.24** — Detect out-of-band modification of managed data in customer storage through manifest checksums, and either apply retention there or detect deletions made by the customer's own lifecycle rules. `[new in v0.7]`
- **CORE 6.25** — Upload files through the browser, CLI or SDK as managed datasets, transferred directly to the project's storage target with resumable multipart uploads and checksum verification, validated by the family plugin and versioned like any other dataset. `[new in v0.8]`
  - *Note:* The original file is kept unchanged; an optimised copy may be derived. Identical re-uploads are recorded as no-ops. Uploads suit reference and sample data; bulk data is connected or registered in place (D4).

#### 7 · Access, tenancy & governance

*Not addressed in the original brief, and among the highest-risk areas of the system.*

- **CORE 7.1** — Organise work into projects with roles and per-workflow permissions.
  - *Note:* Projects sit within a tenant, which for an enterprise is the whole organisation and is the unit of hard isolation (D9). Scope is enforced on every access path from the first slice (D30).
- **CORE 7.2** — Share a workflow or a run read-only, inside or outside the organisation.
- **CORE 7.3** — Store credentials centrally and inject them at execution without exposing them in logs, artifacts, or the definition. `[cross-discipline]`
- **CORE 7.4** — Audit who changed a definition, who ran what, and who accessed which dataset.
- **CORE 7.5** — Enforce quotas on compute, storage, and concurrency per project.
- **CORE 7.6** — Run untrusted user-supplied containers without letting one tenant reach another's data, credentials, or network. `[shapes the core]`
  - *Note:* Decided (D5): hostile multi-tenancy belongs to the paid cloud edition; open-source deployments are operated by their owners. The executor abstraction must still let the cloud edition plug in sandboxed runtimes, because sandboxing cannot be added to a running multi-tenant cluster at acceptable cost.
- **CORE 7.7** — Mint storage credentials inside the environment that owns the data, so that a hosted control plane never holds credentials for customer storage. `[shapes the core]` `[new in v0.7]`

### Data engineering (DE) — 36 capabilities

The discipline with the most mature incumbent tooling. Migration is driven by lineage, reproducibility and backfill ergonomics rather than by the authoring interface, which is where the project's stated contribution lies. Scope should be set accordingly.

#### 1 · Ingestion

- **DE 1.1** — Connect to operational databases, warehouses, object storage, SaaS APIs, message queues, SFTP, and flat files.
  - *Note:* Connector coverage is an unbounded long tail. A connector SDK is a higher priority than a large first-party connector set.
- **DE 1.2** — Extract incrementally, persisting watermark or cursor state between runs. `[shapes the core]`
  - *Note:* A task that retains its position between runs is stateful, which a pure DAG does not accommodate. Decided (D37): no separate state store; the cursor is the end position recorded by the last committed extraction run.
- **DE 1.3** — Capture change from a source: log-based CDC where available, query-based polling otherwise.
  - *Note:* Each connector declares its change-detection strategy; the platform shows whether it captures hard deletes and offers periodic full-snapshot reconciliation where it does not (D37).
- **DE 1.4** — Bootstrap a full historical load and hand over cleanly to incremental extraction.
- **DE 1.5** — Respect source rate limits, paginate, and resume a partially completed extraction.
  - *Note:* Resumption uses the task run's checkpoint slot (D31).
- **DE 1.6** — Sense file arrival by path pattern and trigger downstream work on it.
- **DE 1.7** — Where data from a mutable source is copied (D35), partition the copy by ingestion time, treat each raw partition as the authoritative snapshot of what was extracted, and rerun downstream work from the raw partition rather than by re-querying the source. `[shapes the core]` `[new in v0.7]`
  - *Note:* Re-querying a mutable table returns its current state, not the state at the original extraction. Re-extraction is therefore an explicit act producing a new version of the raw partition. Downstream curated datasets are partitioned by event time with a declared lateness window (D13). Whether a source is copied is the author's explicit choice, with no default (D35). An ephemeral read is repeated at run time, may be fused into downstream transformations, and caps dependent runs at Traceable when the source is unversioned (D4, D35).

#### 2 · Transformation

- **DE 2.1** — Push SQL transformations down to the warehouse rather than pulling data into the platform. `[shapes the core]`
  - *Note:* For warehouse-scale data this determines whether the product is viable. It also introduces a node whose execution is a query submission rather than a container. Built-in Ibis nodes are pushed down when their inputs share one warehouse (D27); the first release targets Postgres and Snowflake (D25), after the first development slice (D29).
- **DE 2.2** — Run distributed transforms on Spark, and mid-size transforms on a single node via DuckDB or Polars.
  - *Note:* Revised in v0.8: DuckDB and Polars form the default in-process runtime (D25). Revised in v0.10: Ibis on DuckDB runs every built-in node, with Polars by exception (D27). Spark is deferred to a later plugin that executes against customer-operated clusters.
- **DE 2.3** — Join, aggregate, pivot, window, and deduplicate as first-class palette operations. `[cross-discipline]`
- **DE 2.4** — Write idempotently: upsert, merge, and partition-overwrite semantics so a rerun does not double-count.
- **DE 2.5** — Maintain slowly changing dimensions and surrogate keys.
- **DE 2.6** — Handle schema evolution: accept additive and widening changes, detect and halt on breaking ones.
- **DE 2.7** — Correctly reprocess late-arriving and out-of-order records into already-published partitions.
  - *Note:* Expressed through partition dependency functions: a raw partition by ingestion day maps onto a window of event-date partitions (CORE 3.9, D13).
- **DE 2.8** — Process continuous streams rather than bounded batches. `[deferred]`
  - *Note:* Deferred (D6). A different execution model — tasks that never finish, watermarks, checkpointed state. Managed long-running streaming jobs may follow later; a native streaming runtime is out of scope.
- **DE 2.9** — Run a pipeline on a short schedule — every few minutes — over only the data that arrived since the last run. `[new in v0.2]`
  - *Note:* Micro-batch, the second step in D6. Covers most "near real-time" needs at minute-level latency without a new execution model; builds on DE 1.2 and CORE 3.3.

#### 3 · Storage & layout

- **DE 3.1** — Write to open table formats — Iceberg, Delta — with ACID commits and time travel.
  - *Note:* Time travel provides dataset versioning at little additional cost, which CORE 6.1 would otherwise have to implement directly.
- **DE 3.2** — Express layered zones (raw, cleaned, curated) as a convention the platform understands and can enforce.
- **DE 3.3** — Declare partitioning and clustering for a target table, and write along those boundaries.
- **DE 3.4** — Compact small files, manage file sizing, and vacuum expired snapshots on a schedule.

#### 4 · Quality & reliability

- **DE 4.1** — Declare tests on data — uniqueness, not-null, referential integrity, accepted values, custom assertions — that can fail a run. `[cross-discipline]`
- **DE 4.2** — Monitor dataset freshness and row-volume anomalies against expectation.
  - *Note:* The freshness expectation is declared by the dataset owner, with a default derived from the production schedule where none is given. A breach is reported against the dataset itself, independently of whether a scheduled run occurred (CORE 6.8, DE 5.8).
- **DE 4.3** — Detect distribution drift on columns between runs. `[cross-discipline]`
- **DE 4.4** — Halt propagation downstream when a quality gate fails, so bad data does not reach consumers. `[shapes the core]`
  - *Note:* Requires the scheduler to distinguish failure from suspension on an upstream quality gate, and to hold rather than retry. Holds are bounded by a configurable timeout, after which the run ends as failed (D31).
- **DE 4.5** — Quarantine rejected records to a dead-letter location and reprocess them once fixed.
- **DE 4.6** — Reconcile source and destination counts or checksums after a load.

#### 5 · Governance

- **DE 5.1** — Resolve lineage at column level, not only at task level — what feeds this field, what breaks if it changes. `[shapes the core]`
  - *Note:* Requires parsing transformation logic rather than observing task edges alone. Feasible for SQL nodes and not achievable inside arbitrary code nodes; the boundary is recorded in D10: derived for parseable nodes, declared or task-level for custom code.
- **DE 5.2** — Catalog datasets with descriptions, owners, tags, and a business glossary.
- **DE 5.3** — Detect, classify, mask, and tokenise personal data.
- **DE 5.4** — Enforce access control at table, column, and row level.
- **DE 5.5** — Apply retention policies and propagate an erasure request through every derived dataset.
  - *Note:* Tractable only where lineage exists, and the clearest commercial justification for the lineage work.
- **DE 5.6** — Agree a data contract between a producing and a consuming workflow, and fail the producer when it breaks the contract.
- **DE 5.7** — Track lineage and rerun work at partition granularity, not whole-dataset granularity. `[shapes the core]`
  - *Note:* Prevents recomputation of a full year to correct a single day. Depends on CORE 3.3.
- **DE 5.8** — Operate a dataset schema in observed mode, where it is inferred and recorded but not enforced, and promote it to an enforced contract with a declared evolution rule when other pipelines begin consuming it. `[new in v0.6]`
  - *Note:* Contract-first declaration would impose ceremony on exploratory work; unenforced schemas would leave production consumers unprotected. The promotion step is the boundary between the two.
- **DE 5.9** — Inherit data classification along lineage, taking the highest sensitivity among a dataset's inputs, and require an explicit, audited assertion by an accountable owner to lower it. `[new in v0.6]`
  - *Note:* Classification here denotes sensitivity and handling — a level such as public, internal, confidential or restricted, plus special categories such as PII, PHI, PCI or export-controlled. Declassification after aggregation or anonymisation is a judgement, never an automatic consequence of a transformation.
- **DE 5.10** — Extend classification and masking to metadata embedded inside files, such as patient identifiers in DICOM headers, with each dataset family exposing its metadata fields for that purpose. `[new in v0.7]`

### Data science (DS) — 31 capabilities

Exploratory and experimental work, delivered largely as a curated palette over established libraries. The value added is that an experiment becomes a reproducible, shareable artifact rather than an untracked notebook. Node granularity — one node per estimator or one node per script — is the open question throughout.

#### 1 · Load & understand

- **DS 1.1** — Load tabular, text, image, time-series, and geospatial data from files, databases, and object storage.
- **DS 1.2** — Infer a schema, enforce it, and coerce types with a record of what was coerced.
- **DS 1.3** — Profile a dataset: distributions, cardinality, missingness, correlations, candidate keys.
- **DS 1.4** — Work against a sample of a large dataset while designing, then run the same graph at full scale. `[shapes the core]`
  - *Note:* Sample-then-scale is the primary interaction loop of the builder, and must be a platform affordance rather than hand-wired by the user.

#### 2 · Prepare

- **DS 2.1** — Clean data: missing values, outliers, duplicates, type repair, text normalisation.
- **DS 2.2** — Reshape: join, aggregate, pivot, explode, window, resample. `[cross-discipline]`
- **DS 2.3** — Encode and scale features as transforms that are fitted on training data only and applied everywhere else.
- **DS 2.4** — Engineer features: derived columns, interactions, binning, date parts, aggregations, text and image featurisation.
- **DS 2.5** — Select features by filter, wrapper, and embedded methods.
- **DS 2.6** — Reduce dimensionality — PCA, UMAP, t-SNE — for modelling and for visualisation.
- **DS 2.7** — Address class imbalance through resampling, synthetic minority sampling, or class weighting.
- **DS 2.8** — Prevent leakage structurally: the platform warns when a graph fits a transform on data the split says it should not see. `[shapes the core]`
  - *Note:* A material differentiator over notebook-based work, possible because the graph makes data flow explicit. It requires the IR to model split semantics rather than ports alone. Revised in v0.10: the platform warns rather than refuses, and the author may override (D36).

#### 3 · Experiment

- **DS 3.1** — Split data by random, stratified, grouped, and temporal strategies.
  - *Note:* The platform warns when a split other than a temporal one is used on time-indexed data, and the author may override (D36). Undetected random cross-validation on a time series is the most common invalidating error in applied work.
- **DS 3.2** — Cross-validate, including nested CV for honest tuning and forward-chaining CV for time series.
- **DS 3.3** — Train traditional supervised models: linear and regularised, tree ensembles, gradient boosting, SVM, kNN, naive Bayes.
- **DS 3.4** — Run unsupervised work: clustering, anomaly detection, association rules, topic models.
- **DS 3.5** — Build time-series models: lag and rolling features, decomposition, classical and ML forecasters, horizon evaluation.
- **DS 3.6** — Tune hyperparameters by grid, random, Bayesian, and successive-halving search, with early stopping of unpromising trials. `[shapes the core]`
  - *Note:* Search over a subgraph is CORE 2.3 fan-out with an added feedback loop: the sampler requires results from completed trials to propose subsequent ones, which a static DAG cannot express.
- **DS 3.7** — Combine models by voting, bagging, boosting, and stacking.
- **DS 3.8** — Load a pretrained model and use it as a node, as a featuriser or as a predictor.

#### 4 · Evaluate & explain

- **DS 4.1** — Compute metric suites appropriate to the task type, with confusion matrices, ROC and PR curves, and calibration plots.
- **DS 4.2** — Compare every model against a naive baseline by default.
- **DS 4.3** — Select a decision threshold against a cost matrix rather than accepting 0.5.
- **DS 4.4** — Analyse errors and residuals, and evaluate performance on slices of the data rather than only in aggregate.
- **DS 4.5** — Explain a model: permutation importance, SHAP, partial dependence and ICE, surrogate models, counterfactuals.
- **DS 4.6** — Audit fairness across protected attributes with standard group metrics.
- **DS 4.7** — Compare runs side by side — parameters, metrics, and artifacts — and quantify whether a difference is meaningful. `[cross-discipline]`

#### 5 · Communicate

- **DS 5.1** — Produce visualisations from any node: distributions, relationships, time series, geospatial, model diagnostics.
- **DS 5.2** — Assemble a run's outputs into a report or dashboard that refreshes when the workflow re-runs.
- **DS 5.3** — Interoperate with notebooks: import a notebook as a pipeline, export a pipeline as one, or open a notebook against a node's output.
  - *Note:* The principal adoption path. Existing notebook practice continues in parallel, so the platform must interoperate with it and provide a defined route to promote a notebook into a pipeline.
- **DS 5.4** — Export figures, tables, and result sets in publication-ready formats.

### Machine learning engineering (MLE) — 25 capabilities

Moving a model from experiment to a scheduled, trusted, replaceable and reversible production asset. This is the point at which the platform becomes a lifecycle system rather than a pipeline tool, and the area where scope is most likely to overrun.

#### 1 · Features & training data

- **MLE 1.1** — Define a feature once and use the same definition for training and for inference.
  - *Note:* Training/serving skew is the most common production failure mode in machine learning. A single definition compiled to both paths addresses it.
- **MLE 1.2** — Retrieve features as of a point in time, so training rows never contain information from after the label event. `[shapes the core]`
  - *Note:* Requires event time and knowledge time. Decided (D38): met by event-time metadata and by publication history or a row-level ingestion timestamp, with a point-in-time join node; no change to the dataset model.
- **MLE 1.3** — Snapshot and version a training dataset so a model's training data can be reconstructed exactly. `[cross-discipline]`

#### 2 · Training at scale

- **MLE 2.1** — Run large parallel sweeps and distributed training jobs under project resource caps.
- **MLE 2.2** — Request, queue for, and share GPUs, including fractional or time-shared allocation. `[shapes the core]`
  - *Note:* GPU scarcity makes queueing policy visible to users in a way that CPU scheduling does not. Directly related to CORE 3.6.
- **MLE 2.3** — Checkpoint a long-running task and resume it after interruption rather than restarting. `[shapes the core]`
  - *Note:* A task with internal resumable state is inconsistent with the stateless-retry model. Decided (D31): rather than a distinct task kind, every task run has an optional checkpoint slot, scoped to the task run and fenced, which the next attempt receives.
- **MLE 2.4** — Tolerate preemptible and spot capacity, resuming automatically after reclamation.
  - *Note:* Resumption uses the task run's checkpoint slot (D31).

#### 3 · Tracking & registry

- **MLE 3.1** — Track every training run: parameters, metrics over time, artifacts, code version, dataset version, environment. `[cross-discipline]`
  - *Note:* Largely derived from CORE 5.2 where provenance is implemented correctly; to be confirmed rather than implemented twice.
- **MLE 3.2** — Register a model version with lineage back to the exact data, code, and run that produced it, and move it through lifecycle stages.
  - *Note:* Models are a specialised dataset type, so registration is publication and model lineage is dataset lineage (D17).
- **MLE 3.3** — Generate a model card from the run — intended use, training data, evaluation, fairness results, limitations.
- **MLE 3.4** — Require approval, and passing evaluation gates, before a model version can be promoted. `[shapes the core]`
  - *Note:* A workflow that pauses for human input is a distinct, long-lived execution state resumed externally. Decided (D31): an approval node's task run is suspended without a lease and resumed through the API; gated publication uses the same state.
- **MLE 3.5** — Package a model for deployment: framework-native, ONNX, or a self-contained container image.

#### 4 · Inference & release

- **MLE 4.1** — Run batch and scheduled scoring pipelines using a registered model version.
- **MLE 4.2** — Deploy a model as a low-latency online endpoint with autoscaling. `[shapes the core]` `[deferred]`
  - *Note:* A long-lived service is not a workflow task, and supporting one extends the product into a serving platform as well as an orchestrator. Decided (D39): out of scope; models are served by external serving systems.
- **MLE 4.3** — Compare a candidate against the incumbent in shadow, canary, or champion–challenger mode.
- **MLE 4.4** — Roll back to a previous model version without rerunning training.

#### 5 · Monitoring & lifecycle

- **MLE 5.1** — Log inference inputs and predictions for later analysis, subject to retention and privacy policy.
- **MLE 5.2** — Detect input drift, prediction drift, and concept drift against the training distribution. `[cross-discipline]`
- **MLE 5.3** — Measure live performance once ground-truth labels arrive, however delayed.
  - *Note:* Labels commonly arrive weeks after the prediction, requiring the same bitemporal joining as MLE 1.2.
- **MLE 5.4** — Trigger retraining on a schedule, on drift, or on performance decay.
- **MLE 5.5** — Run the full retrain → evaluate → gate → promote loop without manual steps, where policy allows it.
- **MLE 5.6** — Alert on model incidents, trace them back to a data or code change, and roll back.

#### 6 · Engineering practice

- **MLE 6.1** — Lint a workflow, unit-test custom nodes, and run the pipeline against sample data in CI on every change. `[cross-discipline]`
- **MLE 6.2** — Promote a workflow across development, staging, and production with environment-specific configuration and connections. `[shapes the core]`
  - *Note:* Environment promotion requires the definition to be separable from its bindings, which is a further constraint on the IR.
- **MLE 6.3** — Specify a task's environment reproducibly through a dependency lockfile resolved to an image digest. `[cross-discipline]`

---

## Catalogue footer

Initial scope. Deep learning and visual neural-network design are excluded by decision; should they be reintroduced, the recommended approach is a plugin that emits a training container rather than a second meaning for the term “node”. Items are capability statements rather than a backlog; the first development slice is set by D29, and further priority and phasing are to follow. The log records thirty-nine decisions (D1–D39) from the scoping sessions; unresolved questions are carried as open items.

---

# Part III · What remains to be discussed

## 1. Proposals raised and not yet confirmed

1. **Two-level warehouse connection policy (amends D28).** D28 states that a connection without compute rights makes pushdown unavailable and the planner extracts instead. In Snowflake, however, reading data at all runs a query on a compute cluster, so a connection with no compute rights cannot be extracted from either. Proposed correction: two levels.
   - **Read:** only the queries needed to extract (column selection and row filters), on the named compute cluster.
   - **Pushdown:** any transformation the planner pushes down.

   Read would be the minimum for any connection the platform uses. Not verified: whether tables stored in Iceberg format can be read directly from their files without Snowflake compute.
2. **Competitive landscape section.** A catalogue section comparing the platform with Dataiku DSS and others. Proposed differentiators: staleness correctness through recorded read positions and hashing; reproducibility that is verified (tiers, comparators, verification runs) rather than asserted; openness (open core, a public IR specification, plugins); text- and git-native definitions with round-tripping; HPC support and portability (run bundles, hybrid agents). Recent decisions align the design with Dataiku in bring-your-own-compute and cross-location behaviour, which the section would need to reflect.
3. **Details recorded in D28 to review.**
   - When a pinned plan can no longer be honoured, the run stops before execution until the author accepts a new plan. The alternative is falling back to the new plan with a warning.
   - How a credit budget is enforced is attached to S22 and not yet defined.
4. **Repartition key (D25, CORE 2.26).** The planner takes the key from the grouping a node declares. The alternative is that authors place repartition steps themselves.

Items 1 and 3 concern warehouses and fall outside the first development slice (D29); they are settled when pushdown is taken up.

5. *Withdrawn.* A first-slice topology decision is unnecessary: with the pull-based agent in every deployment (D29) and isolation enforced from the start (D30), topologies differ only in where the control plane runs, provided the protocol is designed to hybrid requirements from the outset (see section 4, item 1). Whether and when a hosted control plane is operated is a roadmap question (section 5, item 15). Fully managed would still add sandboxing between tenants (CORE 7.6), metering and billing.
6. *Confirmed and recorded in D37* (incremental extraction state).
7. *Confirmed and recorded in D38* (point-in-time retrieval).
8. *Confirmed and recorded in D39* (online model serving excluded).
9. *Confirmed and recorded in D30* (unreadable entities hidden by default).
10. *Confirmed and recorded in D36:* retention governed by ordinary policy, decay warnings opt-in, a single reproducibility setting per project with per-workflow override, the D11 local-backend restriction to be reconsidered, and leakage and temporal-split guards as overridable warnings.

The narrowed Ibis spike proposed here in an earlier draft of v0.10 has been confirmed and is recorded in D27.

## 2. Conditions and follow-ups attached to decisions

| Source | Follow-up |
|---|---|
| D27 | **Spike (condition for full confirmation):** classify each candidate built-in node into the four Ibis-first tiers and so derive the Polars exceptions; run the nodes on DuckDB, including operations larger than memory under a fixed memory limit; check that they compile for Postgres and Snowflake; and review the Ibis project's maintenance and release practices. |
| D27 | PySpark compile check, deferred until a Spark engine is taken up. |
| D26 | Placement constraints and residency: the IR block, dataset-level rules, constraint resolution, capacity conflicts, and the transition for existing workflows (a warning-only phase was suggested). The "Considered" ideas await a decision. |
| D5 | Licence, open/paid line, and bring-your-own AI keys. The licence must be chosen before the first public release or first external contribution. With bring-your-own-compute as the primary model, managed infrastructure is no longer the main paid offering, so the commercial line should be revisited when this is taken up. |
| D22 | A warehouse-native container service as a backend for customers whose only compute is a warehouse. |
| D25 | Spark, Flink and Ray against customer-operated clusters. Identification of the Polars exceptions through the D27 spike, before the palette is designed. |
| D12 | A minimal long-running execution, to be built as a proof that the streaming seams hold. |
| D11 | A local worker or standalone installation, if adoption data shows the container requirement is costing users. |
| D8 | Tune the 1 GB canonical-hashing threshold from measurements. |
| D9 | Hard isolation boundaries inside a tenant must remain possible. |
| D17 | Later dataset families: audio and video, multidimensional arrays, geospatial, graphs, reports. Publication of the family plugin interface as a stable API. |
| D18 | Taking presentation and semantic capabilities from different plugin implementations. |
| D19 | Renames with aliases and transfers between projects. |
| D24 | Cross-project materialisation requests and automatically enforced freshness policies. |
| D29 | After the first slice: the other five dataset families, HPC agents and cloud batch, warehouse pushdown with connection policy, and the remaining deployment topologies. Licence before the repository is made public. |
| D30 | Enforcement mechanism (Postgres row-level security or a mandatory application scoping layer) and the role model, with the control-plane design. |
| D31 | Up-front or batched creation of task runs under large maps, with scheduler capacity (S4). Override roles for quality-gate holds (S18). Default retention of quarantined versions (S15). |
| D33 | A cost-informed fusion policy using measured cost and change frequency from run history. |
| D34 | The estimation method for working sets; capacity as the selection step between engines at one location, applied when Spark or another such engine is added. |
| D38 | The point-in-time join node, designed with the palette; whether extraction stamps a row-level ingestion timestamp by default. |

## 3. Open items

Questions anticipated by the design but not yet resolved. S9–S14 are resolved (see the decision log).

**Behaviour at scale**

- **S1 · Retention cost of reproducibility.** Default retention periods, guidance on when an author should copy a source rather than read it ephemerally (D35), and which budget carries the cost.
- **S2 · Verification cost at scale.** The default verification level, the policy for selecting which runs are verified, and how a partial verdict is represented.
- **S3 · Preview and inspection generation.** Sample sizes and sampling method per artifact type, and the retention period for preview data.
- **S4 · Scheduler load under large fan-out.** The target fan-out the scheduler must sustain, the batching strategy for state writes, and lease renewal intervals; and up-front or batched creation of task runs under large maps (D31).
- **S5 · Metadata and log growth.** Archival thresholds and destinations, retention periods per data class, and the query paths that must remain fast against archived history.
- **S6 · Data locality and egress** *(deferred with D26)*. Whether placement constraints are first-class in the IR or supplied by the backend abstraction, and how a conflict between placement and available capacity is resolved.
- **S7 · Skew and stragglers.** Whether rebalancing is automatic or advisory, and what skew diagnostics are surfaced on the canvas and in run history.
- **S8 · Out-of-memory escalation.** The escalation ladder and its ceiling, whether escalation is enabled by default, and how the escalation is reflected in cost attribution and in the run record.

**Data lifecycle**

- **S15 · Retention defaults and legal holds.** Per-layer defaults and who may place or lift a hold; the default retention of quarantined versions (D31).
- **S16 · Deprecation and deletion.** Notice periods and the override path for urgent deletion.
- **S17 · Breaking schema changes.** The default strategy and how long parallel versions are maintained.
- **S18 · Overriding a failed quality gate.** Required roles and whether an override expires; the mechanics are recorded in D31.
- **S19 · Access control and visibility.** Visibility rules for catalogue entries, lineage nodes and previews, beyond the default of hiding unreadable entities (D30).
- **S20 · Sharing across projects and tenants.** The sharing model, its interaction with cache scope (D9), and revocation.
- **S21 · Lineage interoperability.** Export only, or import as well, and at what granularity.
- **S22 · Cost attribution per dataset.** The attribution method for shared upstream work. Now also covers enforcement of warehouse credit budgets (D28).
- **S23 · Data residency** *(deferred with D26)*. Enforcement at storage, at placement, or both.

**Authoring and execution**

- **S24 · Dynamic output schemas.** Whether such nodes must declare their output columns in advance, may be marked as resolved at run time with downstream schemas shown as pending until a first run, or both; and how validation, contracts and column-level lineage treat a schema known only after execution.

## 4. Pre-development triage

Which questions must be settled before development begins, and which can wait until the work reaches them. An item blocks the start of development only if the first code would build it into something expensive to change later: a persisted schema, the wire protocol that runs inside customer environments, or the IR format that users commit to git. An item whose later correction only costs performance, such as extra cache misses, or is purely additive, waits.

**Settled in the first round (v0.10).** First development slice (D29); isolation enforced from the start (D30); execution state model (D31); execution unit structure (D32); automatic fusion (D33); node-level cache keys (D8); Ibis on DuckDB for every built-in node (D27); capacity checks in place of declared sizes (D34); explicit storage choice for external sources (D35); data-engineering practice first (D36); incremental extraction state (D37); point-in-time retrieval (D38); online serving excluded (D39); default visibility (D30). The licence is deferred until the repository is made public (D5, D29).

**Still to settle before development.**

1. **Protocol between the control and data planes.** Pull-based leasing, heartbeats, fencing tokens, commit requests, buffering during a control-plane outage, credential scoping and protocol versioning. Designed to hybrid requirements in every deployment, so that topologies differ only in where the control plane runs: agent enrolment and authentication, transport security, tolerance of latency and disconnection, version negotiation under skew between agents and control plane, storage credentials minted by the agent, telemetry routed through the agent, and filtering of what crosses to the control plane by classification. *(D15, D21, D22, D29, D30, CORE 2.11, CORE 2.18, CORE 4.7, CORE 7.7)*
2. **Core IR schema.** Schema versions and migrations; enforcement of the semantic/operational split; the node-type contract (runtime, execution modes, supported dialects, declared grouping keys, memory class and order dependence); a port type system with room for split semantics (DS 2.8); schemas known only after a run (S24); separation of definitions from environment bindings (MLE 6.2); version pinning of referenced workflows; and the canonical text syntax, YAML or Python, since round-tripping is in the first slice. *(D3, D29, D31, CORE 1.2, CORE 1.4, CORE 1.6, S24, MLE 6.2)*
3. **Dataset and read-position persistence.** How snapshots, partition versions, manifests and files are stored and related, and how the range of positions consumed is represented. *(D4, D12 Seams 4 and 5, D13, D15, D23, CORE 5.9, CORE 6.7, CORE 6.9)*
4. **Scheduler capacity and queue model.** Target fan-out per run, concurrent task runs and lease interval (S4); fair-share queues across tenants and projects, with backfills in a lower priority class; up-front or batched creation of task runs under maps. *(S4, D20, D31, CORE 3.6)*
5. **Minimum technology stack.** Control-plane language, API style, Postgres migration tooling, confirmation of Python for the unit runtime, and the frontend and canvas framework, since the canvas is in the first slice. *(Part I, section 4)*
6. **Isolation mechanism and role model.** *(D30)*

**Decided seams the first schema must include.** Tenant identifier on every entity (D5); immutable dataset identifier (D19); schema version in the IR (D3); separate semantic and operational fields (D8); phase separate from outcome (D12 Seam 1, D31); failure classes on attempts, checkpoint slots on task runs and the reused outcome (D31); memory class on node types (D34); execution-mode field on node types (D12 Seam 3); read positions consumed (D12 Seam 4); metrics as time series (D12 Seam 10); backend lifecycle interface (D12 Seam 9); attempt-scoped staging with fencing tokens on commits (D15); backend and region of every attempt and artifact (D26 Seam 1); eligibility filter on cache hits (D26 Seam 2); placement and its reason recorded by the planner (D26 Seam 3); query and job tagging (D28); byte and row counts per partition on every manifest, and capacity ceilings per backend (D34); extension interfaces for authentication, policy, audit and AI (D5).

**Settled when the work reaches them.**

| Item | Settled before |
|---|---|
| Ibis spike (D27) | Any built-in relational node or palette design |
| Minimal long-running execution (D12) | Declaring the execution model settled; an early milestone |
| Authentication and identity provider | Multi-user interface work |
| Image builder and registry | CORE 1.10 |
| Observability stack | The log and metrics pipeline |
| Engine family in the cache key (D25) | Cache implementation; an error only causes extra misses |
| Split semantics for leakage prevention (DS 2.8) | The data-science palette; the IR leaves room for it |
| Two-level warehouse policy, pinned-plan behaviour, repartition key (section 1) | Warehouse pushdown and planner work, outside the first slice |

**Set aside.** Retention (S1, S15), verification sampling (S2), preview sample sizes (S3), archiving (S5), placement and residency (S6, S23, D26), skew and memory escalation (S7, S8), deprecation, breaking changes and gate overrides (S16 – S18), visibility and sharing (S19, S20), lineage export (S21), cost attribution (S22), the open/paid line (D5), and the deferred follow-ups of D11, D17, D18, D19, D22, D24 and D25. The competitive landscape section is an addition to this document, not a design question; the mismatch between the code-node lists of CORE 1.8 and D25 was corrected in v0.10.

## 5. Remaining design agenda

In a suggested order. Each topic is expected to produce decisions, capability lines or open items in the catalogue.

1. **Control plane and domain-driven design.** Bounded contexts (authoring and IR, orchestration and scheduling, dataset catalogue, provenance, execution and dispatch, identity and tenancy, plugin registry); aggregates and invariants; the scheduler, reconciler, dispatcher and planner, including placement under D25–D28 and the repartition step; lease and fencing mechanics; state-machine mechanics, building on the model recorded in D31; concurrency model; event flow.
2. **IR specification.** Schema, versioning and migrations; the text syntax (YAML or a Python SDK); round-trip fidelity; split semantics for leakage prevention (DS 2.8); environment bindings for promotion (MLE 6.2); the node-type contract, including declared runtime, execution modes, supported dialects, declared grouping keys, memory class and order dependence (D27, D34).
3. **Execution backends.** The backend interface in detail; Kubernetes and Slurm adapters; the agent protocol (pull-based, outbound-only); image building and registries in the customer's environment (CORE 1.10, D22); job tagging on every backend (CORE 4.8).
4. **Warehouse adapter.** The interface covering pushdown, extraction to Arrow, publication (D15), time-travel replay (D4), credential minting (D22), connection policy (D28) and query tagging; the Snowflake implementation; the conformance-matrix harness and CI accounts.
5. **Node SDK and palette.** The built-in palette per discipline with each node assigned to an Ibis-first tier (D27); the plugin SDK; UI forms from parameter schemas.
6. **Visual builder UX.** Canvas behaviour; sample-then-scale (DS 1.4); showing units and fusion; plan, engine, placement and capacity-check visibility, including extraction suggestions and pinned-plan differences; fused-node inspection.
7. **Security and identity.** Authentication, RBAC and ABAC, secrets, sandboxing of untrusted containers (CORE 7.6), audit.
8. **Technology stack selection.** The undecided items in Part I, section 4.
9. **Observability implementation.** Logs, metrics, events, alerting, cost attribution (CORE 4.5, S22).
10. **Discipline specifics.** DE (connectors, CDC, SCD, idempotent writes); DS (leakage prevention, tuning loops per DS 3.6); MLE (the point-in-time join node of D38, approvals, retraining loop, checkpointing per MLE 2.3).
11. **Reproducibility implementation.** Verification policy (S2), comparator plugins, run bundles (CORE 5.6).
12. **APIs.** Public REST or gRPC, CLI, SDK.
13. **Business model and open-core line** (D5), revisited in light of bring-your-own-compute.
14. **Non-functional requirements.** Scale targets (S4, S5), SLAs, availability.
15. **Roadmap and phasing.** Beyond the first development slice (D29): v1, then v2, including whether and when a hosted control plane is operated.
16. **Open items.** S1–S8 and S15–S24.
