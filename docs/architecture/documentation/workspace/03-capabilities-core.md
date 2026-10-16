## Core platform (CORE)

What the platform must let a user do, stated as capabilities rather than components. Each line is stated so that it can be accepted, deferred or removed individually before any of it becomes architecture.

- **Four sections, not three.** The three disciplines sit on top of a shared substrate — scheduling, execution, provenance, artifacts. That substrate is section **CORE**. A capability required by more than one discipline belongs in that section; otherwise it is implemented three times.
- **Two markers carry meaning.** `[shapes the core]` means the item imposes a requirement on the scheduler or domain model and is expensive to retrofit — these are the ones to settle first. `[cross-discipline]` means the same capability is demanded from more than one direction. `[deferred]` marks a line a decision has pushed out of the initial scope.
- **Decisions are referenced by number, open items by S number.** The decision log records what has been settled and what remains open; the open items carry forward unresolved questions of behavior at scale, of the data lifecycle and of authoring and execution. Catalog notes reference both where they affect a line.
- **Most items are wrapping, not inventing.** Nearly everything under DS and MLE exists in sklearn, Polars, Optuna, SHAP, MLflow. The product is the palette and the reproducibility guarantees around them, not reimplementations. Items requiring original implementation are identified in the notes.
- **IDs are stable.** Items are referenced by ID in review and correspondence — `DE 1.3`, `CORE 2.6` — and are never reused.

Deep learning and visual neural-network design are excluded by decision; should they be reintroduced, the recommended approach is a plugin that emits a training container rather than a second meaning for the term “node”. Items are capability statements rather than a backlog; priority and phasing are in the [roadmap](11-roadmap.md).

The substrate all three disciplines run on. Everything here is discipline-agnostic by construction — if an item only ever serves one discipline, it has been filed under that discipline instead.

### 1 · Authoring

*Constructing and evolving a pipeline definition.*

- **CORE 1.1** — Assemble a pipeline on a canvas as a graph of typed nodes with declared inputs and outputs.
- **CORE 1.2** — Validate a graph before it runs: cycles, unbound parameters, incompatible port types, missing credentials, unsatisfiable resource requests.
  - *Note:* Validation at author time, rather than failure part-way through a run, largely determines the perceived quality of the builder.
- **CORE 1.3** — Parameterize a workflow and supply values per run, with typed defaults and validation.
- **CORE 1.4** — Nest a workflow as a single node inside another workflow. `[shapes the core]`
  - *Note:* Composition keeps a visual graph legible beyond roughly 30 nodes. A referenced workflow is inlined into the parent run, pinned to a version, with each task run recording its origin ([D31]({workspace}/decisions/Platform#31)). Composition does not determine fusion ([D33]({workspace}/decisions/Platform#33)).
- **CORE 1.5** — Version a workflow definition, diff two versions visually, and roll back.
  - *Note:* Canvas edits autosave as drafts; a commit, or a platform-held version in a project without git, is created only when the author commits ([D45]({workspace}/decisions/Platform#45)).
- **CORE 1.6** — Round-trip between the visual graph and a text definition that can be committed to git. `[shapes the core]`
  - *Note:* Required by the engineering audience. Round-trip fidelity, rather than one-way export, is the meaningful capability, and it constrains the IR design substantially. Decided ([D41]({workspace}/decisions/Platform#41)): a strict YAML subset, git authoritative, three-way merge on the semantic model, and a layout sidecar. Canvas edits are autosaved as drafts and committed only when their author chooses, and the platform deploys workflow changes from the branch it deploys from, holding back changes to governed settings until an authorized person approves them ([D45]({workspace}/decisions/Platform#45)).
- **CORE 1.7** — Publish, share, fork, and re-run a workflow template from a catalog.
- **CORE 1.8** — Drop in a custom code node — Python, SQL, or shell — with its own dependency spec.
  - *Note:* The required escape hatch: visual tools without one are abandoned at the first unsupported operation. Code nodes are offered as SQL and Ibis, both eligible for pushdown ([D27]({workspace}/decisions/Platform#27)), Polars and pandas, in-process, and container commands for command-line tools, all on equal terms ([D25]({workspace}/decisions/Platform#25)).
- **CORE 1.9** — Register a third-party plugin node: declared interface, container image, parameter schema, UI form.
  - *Note:* Node ports declare data types, never format plugins, so a node works with any dataset of the declared type. Connectors to source and target systems are node plugins ([D18]({workspace}/decisions/Platform#18)). A connector may implement an optional probe returning a source's current version or position ([D49]({workspace}/decisions/Platform#49)).
- **CORE 1.10** — Declare a node's dependencies as packages and let the platform build, cache and pin the container image, instead of writing Dockerfiles.
  - *Note:* Prebuilt base images for Python, R and common scientific tools keep builds fast. The resolved lockfile and resulting image digest become part of the run record ([D11]({workspace}/decisions/Platform#11)). Builds and the registry may run in the customer's environment ([D22]({workspace}/decisions/Platform#22)).
- **CORE 1.11** — Declare the execution modes a node type supports, and refuse a graph that uses a node in a mode it does not implement.
  - *Note:* Every node type declares `[batch]` in the initial scope ([D12]({workspace}/decisions/Platform#12), Seam 3).
- **CORE 1.12** — Define each built-in node once, as an Ibis expression — eligible for pushdown to a warehouse unless it relies on in-process functions — or in Polars by justified exception, and conformance-test every Ibis node against DuckDB and each supported warehouse dialect. `[shapes the core]`
  - *Note:* One implementation per node; a node that cannot be compiled for a dialect declares the dialects it supports. Moving a node between Ibis and Polars is a new node version ([D25]({workspace}/decisions/Platform#25)). Pushable nodes are Ibis expressions rather than portable SQL text, and every built-in node is Ibis first, through four tiers, with Polars implementations as justified exceptions ([D27]({workspace}/decisions/Platform#27)).

### 2 · Execution

*Turning a definition into running work.*

- **CORE 2.1** — Execute a workflow and observe per-task state transitions in real time.
- **CORE 2.2** — Run independent branches concurrently, bounded by workflow, project, and cluster limits.
  - *Note:* Limits are applied at admission, with fair share deciding order within them ([D43]({workspace}/decisions/Platform#43)). A Maintainer may set limits below the project's quota ([D47]({workspace}/decisions/Platform#47)).
- **CORE 2.3** — Fan a node out over a collection and gather the results back into one downstream input. `[shapes the core]` `[cross-discipline]`
  - *Note:* Scatter/gather over 10,000 items is routine for sequencing workloads and parameter sweeps, and it determines how task state is stored and how the run aggregate is sized. Task runs under a map are created in windows sized to its parallelism and tracked by a map-group record, within the scale targets of [D43]({workspace}/decisions/Platform#43). Nodes in a map's body that do not depend on its item are hoisted out and run once ([D47]({workspace}/decisions/Platform#47)).
- **CORE 2.4** — Declare per-task resources: CPU, memory, GPU, ephemeral disk, wall-clock timeout.
  - *Note:* Ephemeral disk includes DuckDB's spill space. Per-backend ceilings bound every request, and the planner checks estimated working sets against them ([D34]({workspace}/decisions/Platform#34)). Requests are estimated from statistics and history, with declared resources as a floor ([D47]({workspace}/decisions/Platform#47)).
- **CORE 2.5** — Define retry policy per task, distinguishing retriable infrastructure failure from terminal task failure.
  - *Note:* Commits carry the attempt identity as a fencing token, so a superseded attempt cannot publish after its retry ([D15]({workspace}/decisions/Platform#15)). Each failed attempt records a failure class; infrastructure failures draw on a platform retry budget separate from the author's policy, and a fenced attempt is not a failure ([D31]({workspace}/decisions/Platform#31)).
- **CORE 2.6** — Skip re-execution when a task's inputs, parameters, code, and image are unchanged. `[shapes the core]` `[cross-discipline]`
  - *Note:* Highest-value feature for iterative work: change one parameter and only that node and its descendants rerun. Also provides resume-after-failure (CORE 2.7) and shared prefixes in sweeps for free. Keys are hybrid: input-addressed for every node, chained through nodes rather than units, plus content-addressed early cutoff for small artifacts ([D8]({workspace}/decisions/Platform#8)). Reuse is within a project by default, across projects of a tenant by opt-in, and never across tenants ([D9]({workspace}/decisions/Platform#9)). Verification runs always bypass the cache. The plan shows expected reuse; the lookup made when each task run is created is authoritative ([D47]({workspace}/decisions/Platform#47)).
- **CORE 2.7** — Resume a failed run from the point of failure, and re-run a single node together with its descendants.
- **CORE 2.8** — Pause, resume, and cancel a run, with graceful drain of in-flight tasks.
  - *Note:* Pausing stops dispatch and lets running attempts finish, after which the run is suspended; canceling signals running attempts at their next heartbeat ([D31]({workspace}/decisions/Platform#31)), which reaches the agent within about one round trip through its long-poll ([D44]({workspace}/decisions/Platform#44)).
- **CORE 2.9** — Target a different execution backend per run or per task — local container, Kubernetes, HPC scheduler, cloud batch. `[shapes the core]`
  - *Note:* Decided ([D3]({workspace}/decisions/Platform#3)): the custom IR compiles down to backends.
- **CORE 2.10** — Branch conditionally, skip a subgraph, and iterate until a condition holds. `[shapes the core]`
  - *Note:* Decided ([D2]({workspace}/decisions/Platform#2)): workflows are control-flow graphs, not strict DAGs. Only structured constructs are permitted, and iterations unroll into an acyclic run trace ([D2]({workspace}/decisions/Platform#2)). Conditions, collections and loop termination are CEL expressions, and nodes carry run rules over upstream outcomes ([D41]({workspace}/decisions/Platform#41)). Loops may carry state between iterations and run inside one unit, workflows may use an n-way switch and branch joins, and reaching a loop's limit is an explicit outcome ([D46]({workspace}/decisions/Platform#46)).
- **CORE 2.11** — Survive infrastructure loss: a run continues correctly after a scheduler restart or a worker node disappearing. `[shapes the core]`
  - *Note:* Implies leases with heartbeats and a reconciliation loop rather than fire-and-forget event handling. Decided ([D47]({workspace}/decisions/Platform#47), [D48]({workspace}/decisions/Platform#48)): a single leader fenced by an epoch, invariants enforced by the database, lease renewals held in memory and treated as renewed after a takeover, and a level-triggered sweep behind every event.
- **CORE 2.12** — Declare that a node has external side effects — writes to an outside system, sends a message, triggers a deployment — so it is never served from cache and is suppressed or redirected during verification runs. `[shapes the core]`
  - *Note:* Without this, a cached "load to warehouse" silently never reloads, and a verification run re-sends the email. In development runs, side-effecting nodes are suppressed unless a non-production environment binds their target, and record what they would have done ([D50]({workspace}/decisions/Platform#50)).
- **CORE 2.13** — Control caching directly: force-rerun a node and its descendants, disable caching per node or per run, set a time-to-live on nodes reading external sources, and pin a cache boundary inside a fused chain or mark a node to run as its own unit.
  - *Note:* Every skipped node indicates the earlier run its output came from, so that a cached result is not mistaken for a fresh one; it is recorded as a task run with the outcome reused ([D31]({workspace}/decisions/Platform#31)).
- **CORE 2.14** — Fuse adjacent nodes into a single execution unit automatically, and show on the canvas which nodes share a unit. `[shapes the core]`
  - *Note:* Fusion only groups nodes with the same image, execution location and compatible resources, and never across control flow, published datasets, outputs used by several units, pinned cache boundaries, reads from copied external sources, side-effect nodes, or where it would create a cycle between units. Fusion is fully automatic behind a replaceable policy, users can only split, and composites play no part in it ([D32]({workspace}/decisions/Platform#32), [D33]({workspace}/decisions/Platform#33)); a loop run inside one unit is the one exception to the rule on control flow ([D46]({workspace}/decisions/Platform#46)).
- **CORE 2.15** — Run an entire workflow locally in a single process, without containers, for development and small data. `[deferred]`
  - *Note:* Deferred ([D11]({workspace}/decisions/Platform#11)). A local worker or a standalone installation may be added later behind the existing backend interface; such runs would be capped at Traceable, or Re-executable with a recorded lockfile, and barred from publishing to datasets with an enforced contract.
- **CORE 2.16** — Offer two distinct rerun actions: re-execute a run exactly as recorded, reading its originally resolved input versions, or run it again on current data.
  - *Note:* Conflating the two is a common source of confusion about why a rerun produced different results ([D14]({workspace}/decisions/Platform#14)).
- **CORE 2.17** — Install and run the complete platform on a single machine through a container-based deployment, for evaluation, development and small teams.
  - *Note:* The entry point in the absence of a container-free mode ([D11]({workspace}/decisions/Platform#11)). Execution is driven by the same pull-based agent as in every other deployment ([D29]({workspace}/decisions/Platform#29)).
- **CORE 2.18** — Run execution agents inside a customer's own cloud account or HPC cluster that connect outward to a hosted control plane, pull work and execute it locally. `[shapes the core]`
  - *Note:* No inbound connectivity into the customer's network is required; only metadata and events cross the boundary ([D22]({workspace}/decisions/Platform#22)). The protocol, identity, high availability and versioning of agents are recorded in [D40]({workspace}/decisions/Platform#40), and the transport and the proofs of identity in [D44]({workspace}/decisions/Platform#44). The same agent serves HPC backends, and is used in self-hosted and single-machine deployments too ([D29]({workspace}/decisions/Platform#29)).
- **CORE 2.19** — Choose where each unit runs from where its data lives: push relational nodes down to the warehouse holding their inputs, process files and uploads in-process, process inputs held in different locations in-process after reducing each warehouse's share by pushdown, never moving data into a warehouse, and show the engine, location and reason for every unit before the run. `[shapes the core]`
  - *Note:* Precedence: explicit override, hard constraints (deferred, [D26]({workspace}/decisions/Platform#26)), dialect capability, data location. Size does not select the engine; extraction beyond a configurable cap asks the author rather than proceeding, and the plan suggests storing data in the warehouse where that would allow pushdown ([D25]({workspace}/decisions/Platform#25)). Once an engine shares a location with the in-process engines, capacity chooses between them ([D34]({workspace}/decisions/Platform#34)).
- **CORE 2.20** — Run DuckDB and Polars nodes together in one execution unit, chaining consecutive nodes on the same engine into a single segment and handing data between engines as Arrow.
  - *Note:* Each engine's optimizer sees a whole segment; memory and thread limits for both engines derive from the unit's allocation. Non-tabular nodes run in Python or container-command runtimes and scale by fan-out ([D25]({workspace}/decisions/Platform#25)).
- **CORE 2.21** — Record the backend and region of every attempt, and a storage location identifying the region of every artifact. `[shapes the core]`
  - *Note:* Required before placement and residency constraints exist, because locations cannot be reconstructed for historical runs and artifacts ([D26]({workspace}/decisions/Platform#26)).
- **CORE 2.22** — Constrain where units run through hard placement requirements, such as region, residency or remaining inside a warehouse, and soft preferences, and reject plans whose hard constraints cannot be met. `[deferred]`
  - *Note:* Deferred ([D26]({workspace}/decisions/Platform#26)). The location record (CORE 2.21), eligibility checks on cache hits and explicit placement in the plan are kept so that this can be added without rework.
- **CORE 2.23** — Set a policy on each warehouse connection: whether the platform may compute in the warehouse, which compute cluster it uses and at what size, and an optional credit budget; treat a connection without compute rights as unavailable for pushdown. `[shapes the core]`
  - *Note:* Set by the warehouse's owner rather than by workflow authors; the planner places units automatically within it ([D28]({workspace}/decisions/Platform#28)).
- **CORE 2.24** — Pin the plan of a production workflow, so that a change in where its units run is reported rather than applied.
  - *Note:* A run whose pinned placement can no longer be honored stops before execution until the author accepts a new plan ([D28]({workspace}/decisions/Platform#28)).
- **CORE 2.25** — Operate entirely on customer-provided compute: a container-capable backend for execution units and the customer's warehouse for pushdown, with the vendor hosting only the interface and control planes. `[shapes the core]`
  - *Note:* Bring-your-own-compute is the primary deployment model ([D22]({workspace}/decisions/Platform#22)). A warehouse alone runs only pushdown work; every other node needs the container backend.
- **CORE 2.26** — Insert a repartition step when a node groups by a key other than its input's partitioning: rewrite the data hash-bucketed by that key, then fan the node out per bucket. `[shapes the core]`
  - *Note:* Lets in-process engines scale partition-local work by any key without a distributed engine. Work that no key can divide remains flagged by the capacity check ([D34]({workspace}/decisions/Platform#34)).

### 3 · Scheduling & triggering

*Deciding when work happens and for which slice of time.*

- **CORE 3.1** — Schedule a workflow on a cron or interval, with timezone and DST handling.
- **CORE 3.2** — Trigger on an event: webhook, file arrival, dataset update, upstream workflow completion.
  - *Note:* Changes to external sources are detected by source probes that the reconciler runs periodically ([D49]({workspace}/decisions/Platform#49)).
- **CORE 3.3** — Treat a run as covering a logical interval, not merely a wall-clock moment. `[shapes the core]`
  - *Note:* "The run for 2026-09-19" must be reproducible tomorrow. Without this, backfills and partition reruns are not expressible at all.
- **CORE 3.4** — Backfill a historical date range with bounded concurrency and per-interval status. `[shapes the core]`
  - *Note:* Intervals commit as they complete; commits carry the backfill identifier and run below scheduled work in priority ([D20]({workspace}/decisions/Platform#20)).
- **CORE 3.5** — Express a dependency from one workflow onto another workflow's output, where neither owns the other. `[shapes the core]`
- **CORE 3.6** — Share capacity fairly: one project's large fan-out must not starve every other tenant. `[shapes the core]`
  - *Note:* Fairness is a scheduler property, not a limit setting. Retrofitting it into FIFO dispatch means rewriting the scheduler. Decided ([D43]({workspace}/decisions/Platform#43)): dominant-resource fair share per capacity domain over decayed usage, with priority classes. Weights are set by the tenant Admin ([D47]({workspace}/decisions/Platform#47)).
- **CORE 3.7** — Constrain overlap: prevent or queue a second run of the same workflow while one is in flight.
  - *Note:* Implemented by partition write leases taken at admission; a queued run waits for the lease ([D43]({workspace}/decisions/Platform#43)). By default runs overlap, serialized per partition, and a write lease is held by the task run across its retries ([D48]({workspace}/decisions/Platform#48)).
- **CORE 3.9** — Declare how a node's output partitions depend on its input partitions — identity, a time window, all available, the latest, or specific values — or let a merge node discover the affected partitions from the data at run time. `[shapes the core]`
  - *Note:* Required wherever one input partition affects several output partitions, such as late-arriving records or rolling windows. Declared mappings let the plan be known in advance; discovered mappings do the minimum work but decide the plan as the run proceeds ([D13]({workspace}/decisions/Platform#13)).
- **CORE 3.10** — Validate that a schedule's logical interval is compatible with the partitioning of the datasets it writes, including timezone, and require an explicit open-partition declaration when runs are finer-grained than partitions.
  - *Note:* Open partitions are appended to by successive runs and become visible as complete only when marked so. Misaligned boundaries are rejected rather than adjusted ([D13]({workspace}/decisions/Platform#13)).
- **CORE 3.11** — Declare, per input, whether a run waits for it, proceeds on its last valid version, skips the interval or fails when the input is stale, failed or missing, and mark inputs as optional where the output can be produced without them. `[shapes the core]`
  - *Note:* Defaults: scheduled runs wait with a timeout derived from the output's freshness expectation, then fail and alert; manual runs proceed on the last valid version with a warning. Waiting holds no compute, and input versions are resolved after the wait ([D16]({workspace}/decisions/Platform#16)).
- **CORE 3.12** — Defer downstream reconciliation while a backfill runs and plan it once over all changed partitions, at completion or at batch boundaries.
  - *Note:* Prevents each downstream partition being rebuilt once per upstream commit inside its lateness window ([D20]({workspace}/decisions/Platform#20)).
- **CORE 3.13** — Declare a backfill as an atomic restatement, staging every interval and committing a single snapshot at the end.
  - *Note:* Ensures consumers never read a mixture of partitions computed under old and new logic ([D20]({workspace}/decisions/Platform#20)).
- **CORE 3.14** — Request that a dataset be made current through a given time, and have the platform plan and run the minimum work across the project's workflows, with every resulting run grouped under the request that caused it. `[shapes the core]`
  - *Note:* Build modes: only this dataset, upstream where modified, all upstream, downstream ([D24]({workspace}/decisions/Platform#24)).
- **CORE 3.15** — Declare a freshness policy on a dataset and have the reconciler keep it satisfied automatically, in place of a schedule; and make materialization requests across project boundaries. `[deferred]`
  - *Note:* Deferred ([D24]({workspace}/decisions/Platform#24)).

### 4 · Observability

*Seeing what happened, while it happens and afterwards.*

- **CORE 4.1** — Tail a task's logs live, and retrieve them from durable storage after the run, with search.
  - *Note:* Two systems behind one interface: a streaming path and an archive path. Logs must not be stored in the metadata database.
- **CORE 4.2** — See CPU, memory, GPU, and I/O usage over the life of each task, against what it requested.
  - *Note:* Peak memory and spill volume also calibrate the planner's capacity estimates ([D34]({workspace}/decisions/Platform#34)).
- **CORE 4.3** — Review run history as a timeline, including queue time versus run time and the critical path.
- **CORE 4.4** — Alert on failure, on SLA breach, and on custom conditions, to email, chat, or webhook.
- **CORE 4.5** — Attribute compute cost to a run, workflow, project, and user.
  - *Note:* Development runs are attributed to their triggering principal and project and marked as development ([D50]({workspace}/decisions/Platform#50)).
- **CORE 4.6** — Retain task metrics as time series over the life of a task rather than as end-of-run summaries.
  - *Note:* Supports straggler and skew analysis now, and lag, watermark skew and backpressure without schema change later ([D12]({workspace}/decisions/Platform#12), Seam 10).
- **CORE 4.7** — Keep logs and metrics within the customer's environment in hybrid deployments, with live tailing proxied through the execution agent.
- **CORE 4.8** — Tag every query the platform runs in a warehouse, and every job it runs on a customer backend, with the platform, workflow and run, and report usage per workflow.
  - *Note:* Makes spend caused by the platform visible in the customer's own query history and infrastructure accounting ([D22]({workspace}/decisions/Platform#22), [D28]({workspace}/decisions/Platform#28), [S22](07-open-items.md#7.22)). Tags carry the run's mode, so development spend is separable ([D50]({workspace}/decisions/Platform#50)).

### 5 · Reproducibility & provenance

*The stated contribution of the project. Everything here is a claim the system has to be able to defend.*

- **CORE 5.1** — Pin every task to an immutable image digest, never a mutable tag, and record the platform and node versions used.
- **CORE 5.2** — Record for every task run: input dataset versions, parameter values, environment, random seeds, and the resolved code revision.
- **CORE 5.3** — Trace any output artifact backwards to every input, task, and parameter that produced it, and forwards to everything derived from it. `[cross-discipline]`
- **CORE 5.4** — Report the reproducibility tier a given run actually achieves, and what stops it reaching the next one. `[shapes the core]`
  - *Note:* Bit-identical output is not a goal ([D7]({workspace}/decisions/Platform#7)). Tiers ([D7]({workspace}/decisions/Platform#7)): Traceable → Re-executable → Reproducible. Undeclared external inputs, runtime installs, unseeded randomness and unordered parallel output each cap the tier. Exposing this as a visible, first-class property is the principal technical differentiator identified to date.
- **CORE 5.5** — Re-execute a historical run exactly as it originally ran, including its original definition version.
- **CORE 5.6** — Export a run as a portable bundle — definition, pinned images, input references, provenance — that a third party can execute elsewhere.
  - *Note:* Supports the portability objective, and requires the IR to be self-contained rather than dependent on platform-internal state.
- **CORE 5.7** — Run a verification rerun of a recorded run and compare its outputs to the original using a comparator for each artifact type — tables ignoring row order with float tolerance, models by predictions on a probe set, metrics within a tolerance. `[shapes the core]`
  - *Note:* The only way to establish the Reproducible tier. Comparators are a plugin point. Verification costs as much as the original run, so it needs a policy: on demand, sampled, or for runs a user marks as important.
- **CORE 5.8** — Register comparators and canonicalizers per artifact type through the plugin mechanism, with configurable default tolerances that are recorded alongside every verdict.
  - *Note:* Built-ins cover tables, metrics, JSON, text and common model types; domain plugins ship their own (e.g. BAM, VCF). Comparison is layered for large artifacts — byte hash, then summary statistics, then full comparison — and the verdict records which level was reached.
- **CORE 5.9** — Record the range of positions consumed from every source — a snapshot identifier, object version or timestamp range — rather than only the identity of the input. `[shapes the core]`
  - *Note:* Required by incremental extraction ([DE 1.2](04-capabilities-de.md)) and by partition-level rerun; the same record generalizes to offset and window lineage if streaming is added ([D12]({workspace}/decisions/Platform#12), Seam 4). Positions in external sources are fixed at run start by source probes where the source allows ([D49]({workspace}/decisions/Platform#49)).
- **CORE 5.10** — Resolve and record the versions of all inputs once at run start, read them under snapshot isolation for the whole run, and allow any input to be pinned to a specific version. `[shapes the core]`
  - *Note:* Every node in a run sees the same input versions regardless of when it starts ([D14]({workspace}/decisions/Platform#14)). This includes external sources that can be read as of a probed position ([D49]({workspace}/decisions/Platform#49)).
- **CORE 5.11** — Declare coherent reads for a workflow, with per-input override, so that inputs are resolved to versions consistent along lineage.
  - *Note:* Prevents joining a derived dataset with a newer version of its own upstream. Where no coherent set exists, the run fails with an explanation or follows its stale-input policy ([D14]({workspace}/decisions/Platform#14), [D16]({workspace}/decisions/Platform#16)).

### 6 · Data & artifacts

*What flows between tasks, and what outlives the run that made it.*

- **CORE 6.1** — Treat a dataset as a first-class object with its own identity, versions, partitions, schema, and owner — independent of the run that produced it. `[shapes the core]` `[cross-discipline]`
  - *Note:* Decided ([D4]({workspace}/decisions/Platform#4)). The single decision that unifies the three disciplines: an ML feature table, an ETL output table, and a genomic alignment file become the same concept. Without it, freshness, data-triggered scheduling, and cross-workflow dependency are all inexpressible.
- **CORE 6.2** — Store artifacts at identity-addressed paths with pluggable object-store backends, each described by a catalog manifest listing its files, byte digests, roles, schema, statistics and, where applicable, a canonical content hash.
  - *Note:* Paths are not content-addressed, which would force a second write of large outputs. Deduplication by digest is optional and asynchronous ([D23]({workspace}/decisions/Platform#23)). Byte and row counts per partition are mandatory statistics ([D34]({workspace}/decisions/Platform#34)).
- **CORE 6.3** — Preview an artifact in the browser — table, chart, image, model summary — without downloading it.
  - *Note:* Previews of large artifacts must be generated at write time rather than on demand, otherwise the interface stalls on multi-gigabyte outputs.
- **CORE 6.4** — Derive lineage from declared reads and writes rather than requiring the user to document it. `[cross-discipline]`
- **CORE 6.5** — Apply retention and garbage-collection policies to intermediates, preserving inputs referenced by provenance beyond ordinary retention where the reproducibility setting is on.
  - *Note:* Versions resolved by a run still in progress are protected until it finishes ([D14]({workspace}/decisions/Platform#14)). Retention is also reproducibility policy: a run drops to Traceable when its inputs are collected ([D7]({workspace}/decisions/Platform#7)). Ordinary retention governs; preserving inputs referenced by provenance beyond it, and warning before decay with an offer to pin inputs, happen only where the reproducibility setting is on ([D36]({workspace}/decisions/Platform#36)).
- **CORE 6.6** — Inspect any node inside a fused execution unit: per-node row counts, schema changes and timings; column profiles; traced row samples that follow the same entities through every node; fitted parameters; and full regeneration of an intermediate on demand.
  - *Note:* Defaults to statistics plus samples; retention is configurable per unit. Inspection applies to every run; development runs choose their fusion mode and how many intermediates to keep, sample runs defaulting to full intermediates ([D50]({workspace}/decisions/Platform#50)). When a fused node fails, a bounded snapshot of its input is kept. Samples and snapshots are real data and follow the same access control and masking as their source datasets.
- **CORE 6.7** — Represent a dataset as an append-only sequence of positions, of which a point-in-time snapshot is one case. `[shapes the core]`
  - *Note:* Keeps partitioned and continuously appended datasets under one model, and admits a retained topic later without redefining dataset versioning ([D12]({workspace}/decisions/Platform#12), Seam 5).
- **CORE 6.8** — Bind a node output to a dataset once, so that every subsequent run publishes a new version automatically; gate publication behind a quality check or approval where required; and promote an existing artifact into a dataset after the fact.
  - *Note:* Publication is declared, not performed per run. Outputs that are not bound remain run-scoped artifacts, subject to retention and absent from the catalog.
- **CORE 6.9** — Declare a dataset's partitioning scheme, and maintain version history per partition so that a publication creates a snapshot which reuses the partition versions it did not write. `[shapes the core]`
  - *Note:* Partitions and versions are independent: a partition is a slice of the key space, a version is state over time. Every successful publication produces a version, including routine incremental runs with no structural change. A rerun producing identical content may be recorded as a no-op where a content hash is available ([D8]({workspace}/decisions/Platform#8)).
- **CORE 6.10** — Enforce a single producer per dataset: exactly one node in one workflow may publish to it, while any number may consume it.
  - *Note:* Prevents racing publications, ambiguous lineage and unclear contract ownership. Multiple sources are combined by one node ([D13]({workspace}/decisions/Platform#13)).
- **CORE 6.11** — Propose a partitioning scheme when a dataset is created, advise on granularity from observed partition sizes, and perform a change of partitioning scheme only as an explicit, owner-initiated migration that revalidates downstream dependency mappings.
  - *Note:* Granularity is the owner's decision; the platform's suggestions are advisory. Physical layout — file sizing, compaction, clustering — is decided by the platform and does not alter the logical model ([D13]({workspace}/decisions/Platform#13)).
- **CORE 6.12** — Publish by staging new data in an attempt-scoped location and making it current with a single atomic commit, recorded in the metadata catalog for managed datasets and by the target's own transaction for external ones. `[shapes the core]`
  - *Note:* Readers resolve data through the catalog, so unfinished writes are invisible. Targets that cannot commit several partitions atomically are reported as partially published rather than concealed ([D15]({workspace}/decisions/Platform#15)).
- **CORE 6.13** — Declare a publication group so that several managed datasets written by one node are committed together or not at all.
  - *Note:* Independent commits remain the default ([D15]({workspace}/decisions/Platform#15)).
- **CORE 6.14** — Mark outputs built on stale, failed or absent inputs as degraded, state the reason, and cascade the marking to every downstream dataset together with its originating cause.
  - *Note:* A consumer several steps away sees the root cause rather than only its immediate input. The marking clears when the output is rebuilt from ready inputs ([D16]({workspace}/decisions/Platform#16)).
- **CORE 6.15** — Support datasets from six families — tabular, semi-structured and records, text and documents, images, genomics and life sciences, and ML artifacts — and accept further families through the plugin interface. `[shapes the core]`
  - *Note:* Formats are handled by family rather than individually; format-specific validation sits within each family ([D17]({workspace}/decisions/Platform#17)).
- **CORE 6.16** — Represent one logical file as a group of physical files with declared roles — primary, index, sidecar — that are versioned, moved, retained and deleted together. `[shapes the core]`
  - *Note:* A BAM requires its index, a VCF its tabix index, a Shapefile several companion files, and some models and arrays are whole directories ([D17]({workspace}/decisions/Platform#17)).
- **CORE 6.17** — Declare linked items within a dataset — paired-end reads, an image and its annotation — and fail validation when one member of a link is missing.
- **CORE 6.18** — Store collections of many small items as shards with a per-item index, while keeping each item individually addressable for preview, lineage and sampling.
  - *Note:* Millions of individually stored objects strain storage and metadata alike ([S5](07-open-items.md#7.5)).
- **CORE 6.19** — Declare whether a dataset's format can be read in ranges, and use that declaration when planning fan-out.
  - *Note:* Parquet and indexed BAM can be split within a file; gzip-compressed CSV and FASTQ cannot, and must be processed file by file.
- **CORE 6.20** — Define each data format as a platform-owned type with a contract schema, a reader protocol and a conformance suite, and accept plugins that implement a type only when they pass its suite. `[shapes the core]`
  - *Note:* A plugin declares a manifest — identity, implemented type, runtime image, file-group layout, links and capabilities — and implements required `validate` and `metadata` functions plus optional ones. It never touches the catalog, storage or interface directly ([D18]({workspace}/decisions/Platform#18)).
- **CORE 6.21** — Bind each dataset to exactly one format implementation at a pinned version, record the binding on every dataset version, and change it only through an explicit migration that revalidates the dataset. `[shapes the core]`
  - *Note:* Upgrades are offered as a bulk action that reports datasets whose validation outcome would change before committing ([D18]({workspace}/decisions/Platform#18)).
- **CORE 6.22** — Let administrators set the allowed format implementations per type at organization or project level, defaulting to one, so that new datasets bind automatically without users having to choose.
- **CORE 6.23** — Store managed datasets on platform storage or on customer storage — object storage in the customer's account, a table in their lakehouse catalog, or a table in their warehouse — with targets set at tenant, project or dataset level. `[shapes the core]`
  - *Note:* Managed describes who owns the lifecycle, not where the bytes sit. Publishing into a customer's lakehouse makes outputs directly usable by their existing tools ([D4]({workspace}/decisions/Platform#4)).
- **CORE 6.24** — Detect out-of-band modification of managed data in customer storage through manifest checksums, and either apply retention there or detect deletions made by the customer's own lifecycle rules.
- **CORE 6.25** — Upload files through the browser, CLI or SDK as managed datasets, transferred directly to the project's storage target with resumable multipart uploads and checksum verification, validated by the family plugin and versioned like any other dataset.
  - *Note:* The original file is kept unchanged; an optimized copy may be derived, and is always derived for a tabular upload where the Iceberg projection is on ([D44]({workspace}/decisions/Platform#44)). Identical re-uploads are recorded as no-ops. Uploads suit reference and sample data; bulk data is connected or registered in place ([D4]({workspace}/decisions/Platform#4)).

### 7 · Access, tenancy & governance

*Not addressed in the original brief, and among the highest-risk areas of the system.*

- **CORE 7.1** — Organize work into projects with roles and per-workflow permissions.
  - *Note:* Projects sit within a tenant, which for an enterprise is the whole organization and is the unit of hard isolation ([D9]({workspace}/decisions/Platform#9)). Scope is enforced on every access path ([D30]({workspace}/decisions/Platform#30)): row-level security on the tenant, with project roles, resource-level bindings and clearance enforced by the authorization layer ([D45]({workspace}/decisions/Platform#45)).
- **CORE 7.2** — Share a workflow or a run read-only, inside or outside the organization.
- **CORE 7.3** — Store credentials centrally and inject them at execution without exposing them in logs, artifacts, or the definition. `[cross-discipline]`
  - *Note:* The control plane stores secret references centrally; values are held in, and resolved by the agent from, the customer's secret manager or a built-in store on the data-plane side, so the control plane never holds them ([D40]({workspace}/decisions/Platform#40)).
- **CORE 7.4** — Audit who changed a definition, who ran what, and who accessed which dataset.
  - *Note:* Authorization decisions on changes and data access are audited, as are commits made on an author's behalf ([D45]({workspace}/decisions/Platform#45)).
- **CORE 7.5** — Enforce quotas on compute, storage, and concurrency per project.
  - *Note:* Quotas are hard ceilings, separate from fair share ([D43]({workspace}/decisions/Platform#43)). They are set by the tenant Admin ([D47]({workspace}/decisions/Platform#47)).
- **CORE 7.6** — Run untrusted user-supplied containers without letting one tenant reach another's data, credentials, or network. `[shapes the core]`
  - *Note:* Decided ([D5]({workspace}/decisions/Platform#5)): hostile multi-tenancy belongs to the paid cloud edition; open-source deployments are operated by their owners. The executor abstraction must still let the cloud edition plug in sandboxed runtimes, because sandboxing cannot be added to a running multi-tenant cluster at acceptable cost.
- **CORE 7.7** — Mint storage credentials inside the environment that owns the data, so that a hosted control plane never holds credentials for customer storage. `[shapes the core]`
