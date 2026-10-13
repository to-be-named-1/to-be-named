## Vocabulary

### Supplementary vocabulary

Terms used throughout that are not given their own entry in the key terms below.

| Term | Meaning |
|---|---|
| Task run, attempt, run trace | One execution of a unit is a task run (a map makes many); each try is an attempt; the run trace records them all and is always acyclic because loops are unrolled. |
| Canonicalizer vs comparator | A canonicalizer normalizes an output so it can be hashed exactly, with no tolerance; a comparator judges whether two outputs are the same result within a tolerance and explains the verdict. |
| Managed vs external dataset | Distinguished by who owns the lifecycle, not by where the bytes sit. |
| Partition vs version | A partition is a slice of the key space; a version is state over time. A snapshot reuses untouched partition versions. |
| Open partition | A partition appended to by successive runs until explicitly marked complete. |
| Partition dependency function | How output partitions depend on input partitions: identity, time window, all, latest, specific values, or discovered at run time by a merge node. |
| Dataset family | A group of formats that behave alike on the platform (tabular, semi-structured, text and documents, images, genomics, ML artifacts). |
| Format type, plugin, binding | The platform defines a format type (for example `genomics/bam` v1); plugins implement types; each dataset is bound to one pinned implementation. |
| Data commit | The atomic act by which the control plane makes an attempt's staged outputs current; defined in the catalog's Key terms. Distinct from a git commit, a database transaction and a table-format commit. |
| Materialization request | A declarative request to make a dataset current through a given time, for which the reconciler plans the minimum work. |
| Engine segment | Consecutive in-process nodes on the same engine, chained so that one optimizer sees them all. The level between node and execution unit ([D32](../../decisions/0032-execution-unit-structure.md)). |
| Phase and outcome | Every run, task run and attempt carries a lifecycle phase (pending, active, suspended, ended) and, separately, an outcome that is empty until the phase is ended ([D31](../../decisions/0031-execution-state-model.md)). |
| Checkpoint slot | An optional location scoped to a task run, not an attempt, into which a unit may write resumable state that the next attempt receives ([D31](../../decisions/0031-execution-state-model.md)). |
| Fusion policy | The replaceable rule that chooses among legal groupings of nodes into units; its version is recorded on every plan ([D33](../../decisions/0033-automatic-fusion.md)). |
| Pushdown | Running a relational node inside the warehouse that holds its inputs, instead of extracting the data. |
| Extraction cap | A configurable limit on data extracted from a warehouse; exceeding it stops the plan and asks the author. |
| Single-node guideline | A threshold beyond which work is flagged as exceeding in-process capacity. Made concrete as the planner's capacity check ([D34](../../decisions/0034-capacity-and-size.md)). |
| Memory class | A node type's declared memory behavior: streaming, blocking and spilling, or blocking and non-spilling ([D34](../../decisions/0034-capacity-and-size.md)). |
| Repartition step | A unit that rewrites data hash-bucketed by a key, so that a node can fan out by a key other than the input's partitioning. |
| Conformance matrix | Built-in relational nodes × engines (DuckDB, Postgres, Snowflake); each cell is a fixture suite checking that the node gives the same answer on that engine. |
| Connection policy | Settings on a warehouse connection, set by the warehouse's owner: whether the platform may compute there, which compute cluster it uses, and an optional credit budget. |
| Plan pinning | Freezing a production workflow's placement so that changes are reported rather than applied. |
| Bring-your-own-compute (BYOC) | The deployment model in which execution runs on customer infrastructure and the vendor coordinates. |
| Draft | An autosaved, uncommitted edit to a workflow or dataset declaration, held by the platform for its author until committed or discarded ([D45](../../decisions/0045-isolation-enforcement-and-role-model.md)). |
| Deploy | The platform's act of making a committed workflow change the version that scheduled and production runs use; for a git-connected project, a commit on the branch the platform deploys from, once any change to governed settings is authorized. Distinct from dataset publication and from the long-lived executions of [D6](../../decisions/0006-streaming.md) and [D12](../../decisions/0012-streaming-readiness.md) ([D45](../../decisions/0045-isolation-enforcement-and-role-model.md)). |
| Clearance | The highest classification whose data content a member may read; roles govern metadata and actions ([D45](../../decisions/0045-isolation-enforcement-and-role-model.md)). |
| Carried state | Values and outputs a loop passes from one iteration to the next, declared on the loop frame ([D46](../../decisions/0046-control-flow-constructs.md)). |
| In-unit loop | A loop whose iterations run inside one execution unit, cached and retried as a whole and resumed from its checkpoint slot ([D46](../../decisions/0046-control-flow-constructs.md)). |
| Capacity domain | A set of agent pools that share physical capacity, such as one cluster; admission and fair share are computed per domain ([D43](../../decisions/0043-scheduling-and-capacity.md)). |
| Input resolution | Choosing, once per run, the versions and positions of the inputs it reads and recording them as identifiers; external sources are resolved by source probes. "Resolve" is used for nothing else: environment names are bound, node-type and workflow versions are pinned, attempts are specified by building their unit specification, and expressions are evaluated ([D47](../../decisions/0047-control-plane-structure.md), [D49](../../decisions/0049-source-probes.md)). |
| Source probe | A platform maintenance unit, run through the agent, that asks external sources for their current version or position so that a run can read them as of it ([D49](../../decisions/0049-source-probes.md)). |
| Run driver | The control-plane component that advances each run through its graph at run time: it creates task runs, evaluates conditions and run rules, decides retries and ends the run ([D47](../../decisions/0047-control-plane-structure.md)). |
| Expected reuse | The units a plan expects to serve from cache, from the keys known at run start; the lookup made when each task run is created is authoritative ([D47](../../decisions/0047-control-plane-structure.md)). |
| Capacity check and admission | The capacity check is the planner's check of one unit's estimated working set against its backend's per-unit ceiling ([D34](../../decisions/0034-capacity-and-size.md), [D47](../../decisions/0047-control-plane-structure.md)); admission is the scheduler's decision that a ready unit's request fits the free capacity of its capacity domain now ([D43](../../decisions/0043-scheduling-and-capacity.md)). |
| Leader epoch | A number incremented at every change of leader; every leader-only write checks it, so a deposed leader cannot act ([D47](../../decisions/0047-control-plane-structure.md)). |
| Held attempt | An attempt whose commit awaits a quality-gate release or an approval; its staged outputs stay durable and the control plane completes the commit later ([D48](../../decisions/0048-execution-mechanics.md)). |
| Hoisting | Moving a node that depends on neither the map item, the loop index nor carried state out of its frame, so that it runs once ([D47](../../decisions/0047-control-plane-structure.md)). |
| Sandbox | A workspace for full-scale development runs: datasets it writes are committed on its own line, visible only to runs in it, while everything else is read from production ([D50](../../decisions/0050-development-mode.md)). |
| Line | The sequence of heads, versions and partition versions a dataset has in production or in one sandbox; a sandbox line shares unwritten partitions with production by reference ([D50](../../decisions/0050-development-mode.md)). |
| Sample run and full-scale development run | The two kinds of development run: one on a sample of its inputs, writing only run-scoped artifacts, the other on full inputs, committing to a sandbox. A preview is a canvas action that starts a sample run of one node ([D50](../../decisions/0050-development-mode.md)). |
| Selection boundary | The edges where unselected nodes feed the nodes a run is asked to execute; unchanged upstream outputs are read there and, in a sample run, sampled there ([D50](../../decisions/0050-development-mode.md)). |
| Referential subsetting | Sampling one driving input by a hash of its key and keeping, in every input joined to it, only the rows whose join key matches, so that joins on the sample keep their matches ([D50](../../decisions/0050-development-mode.md)). |
| Session unit | A warm container for one author, project, image and pool that runs successive interactive sample runs, each unit in a fresh process ([D50](../../decisions/0050-development-mode.md)). |

### Key terms

Vocabulary the rest of the documentation depends on. Each core concept is given a definition, a diagram of the underlying mechanism and a worked example based on a customer-churn pipeline used as the running example throughout.

##### IR — *intermediate representation*

The platform's **canonical, machine-readable definition of a workflow**: its nodes, their typed inputs and outputs, the edges and control-flow constructs between them, parameters, resource requests, pinned image digests, and retry, caching and side-effect declarations. The term comes from compilers, where the IR sits between the language people write and the code machines run.

The IR is **the single source of truth**. The canvas, the git-committed text form and imported templates are all views of it; backend submissions are all generated from it. Validation, cache keys, provenance records, version diffs and reproducibility checks all operate on the IR — never on canvas state or on a backend's own format. It is custom to this platform ([D3](../../decisions/0003-ir-and-execution-engines.md)) and carries its own schema version. For a project connected to git, the YAML file in git is the authoritative stored form of the IR; the canvas reads it and changes it through drafts that their author commits ([D45](../../decisions/0045-isolation-enforcement-and-role-model.md)), and keys are computed over its normalized semantic model, not its text ([D41](../../decisions/0041-ir-text-form-round-trip-and-structure.md)).

> *Diagram:* Authored in: Visual canvas, YAML in git (a Python SDK generating IR follows, [D41](../../decisions/0041-ir-text-form-round-trip-and-structure.md)), Template import → **IR** (validated · versioned · hashed) → Compiled to: Kubernetes, HPC (Slurm), Local containers, Export: Argo / Airflow

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

Only semantic fields feed cache keys and reproducibility checks ([D8](../../decisions/0008-cache-keying.md)), so changing memory or moving a node on the canvas never invalidates a result.

#### Workflow structure

##### Node — *what the user draws*

One operation on the canvas, with typed inputs, typed outputs and parameters — what a user would call a **step**. Nodes describe *what* should happen; they say nothing about how the work is packaged for execution. Granularity is chosen by context ([D1](../../decisions/0001-node-granularity.md)).

- **Fine-grained.** One small operation: a scaler, a join, drop nulls.
- **Coarse.** A large unit of work: a script, a SQL query, a tool such as BWA-MEM.
- **Composite.** A subworkflow collapsed into one node for readability and reuse.
- **Control-flow.** `if`, `map`, `loop`. Compute nothing; decide what runs next.

**Composition** is the user action that creates a composite node. It shapes the canvas only: at compile time a composite is flattened back into its inner nodes, and execution is planned from the flattened graph. Composition never implies fusion: a composite may become one execution unit, several, or part of a unit shared with nodes outside it ([D33](../../decisions/0033-automatic-fusion.md)).

> *Diagram: A composite node on the canvas is flattened into its inner nodes at compile time; control-flow and other nodes pass through unchanged.*
>
> The composite **prep** node exists only on the canvas. At compile time it dissolves into **clean → impute → encode**; execution units are then formed from the flattened graph. The **map** is a control-flow node: it computes nothing itself, it instructs the orchestrator to run **train** 200 times.

> **Example.** The churn pipeline shows four nodes on the canvas: **extract** (a SQL query), **prep** (a composite the user collapsed), a **map** over 200 hyperparameter sets wrapping **train**, and **evaluate**. Clean, impute and encode are not visible on the canvas unless the composite is opened; the compiler always resolves them.

##### Execution unit — *what the orchestrator dispatches*

The smallest thing the orchestrator **schedules, retries, caches and records provenance for**. One or more nodes compiled into a single job that reads its inputs from storage, runs its nodes in one container, writes its outputs to storage and exits; a sample run started from the canvas may instead run it as a fresh process in a warm session container ([D50](../../decisions/0050-development-mode.md)). Inside the unit, nodes are grouped into **engine segments** — consecutive nodes on one engine, such as a DuckDB query, a Polars lazy plan or a Python block — which hand data to each other in memory as Arrow ([D32](../../decisions/0032-execution-unit-structure.md)).

- **One container, one image.** The runtime belongs to each segment, not to the unit.
- **One resource request.** CPU, memory and GPU on one backend.
- **Stored in, stored out.** Intermediates between its nodes stay in memory.
- **Atomic.** Succeeds or fails as a whole; safe to re-run.

> *Diagram: The churn pipeline's eleven nodes compile into five execution units; outputs are stored only between units.*
>
> Eleven nodes, five execution units. Inside a unit, data passes between nodes in memory; outputs are written to storage only at the boundaries between units. **U5** stands alone because it writes to an external system.

At run time, one compiled unit can execute many times. Each execution is a **task run**; each try at a task run is an **attempt**. The record of every task run and attempt that actually happened is the **run trace** — always acyclic, because loop iterations are unrolled into separate task runs ([D2](../../decisions/0002-graph-model.md)).

> *Diagram: One execution unit becomes many task runs under a map, and each task run can have several attempts.*
>
> One compiled unit, many executions. A **map** turns U3 into 200 task runs. When task run 17's machine is lost, its lease expires and a **retry** creates attempt 2 of the same task run.

> **Example.** Change `max_depth` on train: U1 and U2 are reused from cache; U3, U4 and U5 rerun. Change a parameter on impute: all of U2 reruns, because impute shares a unit with its neighbors — cheap here, and if impute became expensive the user could pin a cache boundary after it and U2 would split in two.

##### Fusion — *grouping nodes into one unit*

Grouping adjacent nodes into one execution unit so they run in one container and never store what passes between them. It exists because every unit pays fixed overheads — starting a container, writing its output, the next unit reading it back, storing the intermediate, a scheduler round-trip — and for cheap operations those overheads dwarf the work itself. **Fusion is what makes fine-grained nodes affordable.** It is applied automatically by the planner; users can only split, by pinning a cache boundary or marking a node to run as its own unit ([D33](../../decisions/0033-automatic-fusion.md)).

> *Diagram: Unfused, four nodes pay four container starts and three write-read round trips; fused, one start and data stays in memory.*
>
> The same four nodes, with and without fusion. ▶ marks a container start. Unfused, every edge is a write to storage and a read back; fused, the edges disappear into memory and only the final output is stored.

> **Example · indicative figures.** A 20-node preparation chain on a 2 GB table, each node doing about half a second of real work. Unfused: 20 × (≈10 s start-up + ≈20 s write + ≈20 s read) ≈ **17 minutes** and 40 GB of intermediates for 10 seconds of computation. Fused: one start-up, one read, one write — **under a minute**.

**Nodes can be fused only when**

- They share an image and execution location ([D32](../../decisions/0032-execution-unit-structure.md))
- Their resource needs are compatible
- No control flow sits between them, unless a loop runs inside one unit ([D46](../../decisions/0046-control-flow-constructs.md))
- No output between them must be stored: a published dataset, an output used by several units, a pinned cache boundary, a read from a copied external source ([D35](../../decisions/0035-ephemeral-extraction.md))
- Neither has an external side effect
- Neither is marked to run as its own unit ([D33](../../decisions/0033-automatic-fusion.md))
- Grouping would not create a cycle between units

**What fused nodes give up, and how it is recovered**

- Per-node caching and retries: a change or failure reruns the whole unit
- Full intermediates: replaced by per-node statistics, traced row samples and fitted parameters
- Any intermediate can be regenerated on demand from the unit's stored inputs
- Development runs choose their fusion mode, automatic or unfused, and how many intermediates to keep (CORE 6.6, [D50](../../decisions/0050-development-mode.md))

#### Caching

##### Caching — *task-output memoization*

Before running an execution unit, the platform computes a **cache key** from everything that determines the unit's output. If an artifact already exists under that key and is still retained, the unit is skipped and the artifact reused. It applies to pipeline iteration, resumption after failure, sweeps with a shared prefix, shared templates and backfills. Verification runs and side-effecting nodes never use it.

> *Diagram: Changing node B changes its key, which changes the keys of C and F; A and E keep their keys and are reused.*
>
> Keys travel along the edges. Editing **B** changes key(B), which is part of key(C), which is part of key(F), so all three rerun. **A** and **E** never involved B, so their keys, and their cached outputs, are unchanged. All of this is known before the run starts.

- **Cache key.** A hash of a node's semantic IR fields — code, image digest, node version, resolved parameters, declared environment — plus the keys of the nodes feeding it, so the key of a stored output depends only on the subgraph that produces it, not on how nodes are grouped into units ([D8](../../decisions/0008-cache-keying.md)). Keys of intermediates inside a unit are computed but never stored or looked up. Operational fields such as resources, backend, labels and canvas layout are excluded, so changing memory or moving a node never invalidates a result.
- **Input-addressed.** Input identity is the upstream *key*. Stable, cheap, and what will rerun is shown before the run starts, as in the diagram above, as expected reuse that the lookup made when each task run is created confirms ([D47](../../decisions/0047-control-plane-structure.md)).
- **Content-addressed.** Input identity is a hash of the upstream *output*. Allows early cutoff, but needs stable output hashing and decides the plan as the run proceeds. Used together with input-addressed keys ([D8](../../decisions/0008-cache-keying.md)).
- **Canonicalizer.** Normalizes an output — sorts rows, strips file metadata — so it can be hashed exactly for content addressing. No tolerance; distinct from a comparator.

> *Diagram: A harmless edit to B reruns everything downstream under input-addressed keys, but only B under content-addressed keys.*
>
> The difference between the two strategies. Editing a comment in **B** changes nothing it produces. Input-addressed keys cannot detect this, so C and D rerun. Content-addressed keys hash B's new output, find it unchanged, and reuse C and D — **early cutoff** — at the price of hashing outputs and not knowing the plan in advance.

**The platform uses both ([D8](../../decisions/0008-cache-keying.md)).** Input-addressed keys are computed for every node, chained through the nodes that feed it, so the plan shows before the run starts which units are expected to be reused; the lookup made when each task run is created is authoritative ([D47](../../decisions/0047-control-plane-structure.md)). In addition, artifacts small enough to hash cheaply get a canonical content hash recorded when they are written; nodes whose stored inputs all carry one also get a content key. A unit is skipped if every one of its stored outputs is found under either key.

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

> **Example · undeclared external input.** The extract node runs `SELECT * FROM customers`. The query text never changes, so neither does its key; without a governing rule the platform would continue to serve the previously cached result indefinitely. The rule: a node reading an external source is not cacheable unless its key includes a version of that source (an Iceberg snapshot, an S3 object version, or the logical interval if data per interval is immutable). Where correct behavior is uncertain, the design prefers a miss.

#### Reproducibility

##### Reproducibility — *a verified, per-run claim*

The platform's ability to re-execute a recorded run and state precisely **how closely the new outputs match the originals, and why** — not a yes/no badge. The goal is the same result, not byte-identical files ([D7](../../decisions/0007-reproducibility-guarantee.md)). A tier belongs to a *run*, not a workflow: fixing a workflow makes future runs more reproducible, never past ones. Tiers are as recorded in [D7](../../decisions/0007-reproducibility-guarantee.md).

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

#### Data

- **Artifact.** Any stored output of an execution unit, often temporary, stored at an identity-addressed path and described by a manifest in the catalog ([D23](../../decisions/0023-artifact-storage-layout.md)).
- **Dataset.** A named, versioned, long-lived data asset with an owner and consumers, independent of the run that wrote it ([D4](../../decisions/0004-datasets-as-first-class-objects.md)). Every dataset version is an artifact or, for an external dataset, a reference; most artifacts never become dataset versions.
- **Logical interval.** The slice of time a run is *for* (e.g. 2026-09-19), as opposed to when it happened to execute. Makes reruns and backfills deterministic.
- **Data commit.** The single atomic act by which the control plane makes the staged outputs of one attempt current in the catalog ([D15](../../decisions/0015-atomic-publication.md), [D21](../../decisions/0021-architecture-planes.md)). An attempt writes its outputs to an attempt-scoped staging location, where they are durable but invisible; the agent then sends a commit request carrying the attempt's fencing token, the staged manifests, the read records and any quality-gate results ([D40](../../decisions/0040-protocol-between-the-control-and-data-planes.md)). The control plane rejects the request if the attempt has been superseded; otherwise, in one database transaction, it records the manifests, the new partition versions and dataset version, the read records and cursor frontier, moves the head of the dataset's line, production or a sandbox ([D50](../../decisions/0050-development-mode.md)), to the new version and writes one outbox row for each subscribed handler ([D48](../../decisions/0048-execution-mechanics.md)). Afterwards, runs that resolve their inputs see the new version. A commit is all-or-nothing, happens at most once per attempt, and is performed only by the control plane; by default it makes one dataset's new version current, and a publication group makes several current together.
  - *Also commits:* an append to an open partition and marking it complete; releasing a quarantined version ([D31](../../decisions/0031-execution-state-model.md)); registering an unbound run-scoped artifact. A fenced write to a task run's checkpoint slot is a **checkpoint commit**, which makes a checkpoint current but creates no dataset version.
  - *Not commits:* writing to staging; a failed quality gate, which records a quarantined version but makes nothing current; a task run or run succeeding, which is an execution outcome ([D31](../../decisions/0031-execution-state-model.md)) — one run may make many commits, as in a backfill ([D20](../../decisions/0020-backfill-commits-and-scheduling.md)), or none; a cache hit.
  - *Distinct terms:* a **git commit** changes workflow definitions ([D41](../../decisions/0041-ir-text-form-round-trip-and-structure.md)); a **database transaction** is the mechanism by which a data commit is carried out; a **table-format commit** (Iceberg, Delta) is a step inside a data commit where the storage target is a lakehouse table ([D15](../../decisions/0015-atomic-publication.md)), whereas the Iceberg metadata projected for datasets on object storage is written after the data commit and is not part of it ([D42](../../decisions/0042-catalog-persistence.md)). Used alone, "commit" means a data commit.
