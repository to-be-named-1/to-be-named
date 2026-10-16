## Data engineering (DE)

The discipline with the most mature incumbent tooling. Migration is driven by lineage, reproducibility and backfill ergonomics rather than by the authoring interface, which is where the project's stated contribution lies. Scope should be set accordingly.

### 1 · Ingestion

- **DE 1.1** — Connect to operational databases, warehouses, object storage, SaaS APIs, message queues, SFTP, and flat files.
  - *Note:* Connector coverage is an unbounded long tail. A connector SDK is a higher priority than a large first-party connector set.
- **DE 1.2** — Extract incrementally, persisting watermark or cursor state between runs. `[shapes the core]`
  - *Note:* A task that retains its position between runs is stateful, which a pure DAG does not accommodate. Decided ([D37]({workspace}/decisions/Platform#37)): no separate state store; the cursor is the end position recorded by the last committed extraction run. The end position of each range is fixed at run start by a source probe ([D49]({workspace}/decisions/Platform#49)).
- **DE 1.3** — Capture change from a source: log-based CDC where available, query-based polling otherwise.
  - *Note:* Each connector declares its change-detection strategy; the platform shows whether it captures hard deletes and offers periodic full-snapshot reconciliation where it does not ([D37]({workspace}/decisions/Platform#37)).
- **DE 1.4** — Bootstrap a full historical load and hand over cleanly to incremental extraction.
- **DE 1.5** — Respect source rate limits, paginate, and resume a partially completed extraction.
  - *Note:* Resumption uses the task run's checkpoint slot ([D31]({workspace}/decisions/Platform#31)).
- **DE 1.6** — Sense file arrival by path pattern and trigger downstream work on it.
  - *Note:* Sensed by source probes that the reconciler runs periodically ([D49]({workspace}/decisions/Platform#49)).
- **DE 1.7** — Where data from a mutable source is copied ([D35]({workspace}/decisions/Platform#35)), partition the copy by ingestion time, treat each raw partition as the authoritative snapshot of what was extracted, and rerun downstream work from the raw partition rather than by re-querying the source. `[shapes the core]`
  - *Note:* Re-querying a mutable table returns its current state, not the state at the original extraction. Re-extraction is therefore an explicit act producing a new version of the raw partition. Downstream curated datasets are partitioned by event time with a declared lateness window ([D13]({workspace}/decisions/Platform#13)). Whether a source is copied is the author's explicit choice, with no default ([D35]({workspace}/decisions/Platform#35)). An ephemeral read is repeated at run time, may be fused into downstream transformations, and caps dependent runs at Traceable when the source is unversioned ([D4]({workspace}/decisions/Platform#4), [D35]({workspace}/decisions/Platform#35)). The raw copy carries its ingestion time as a column ([D44]({workspace}/decisions/Platform#44)).

### 2 · Transformation

- **DE 2.1** — Push SQL transformations down to the warehouse rather than pulling data into the platform. `[shapes the core]`
  - *Note:* For warehouse-scale data this determines whether the product is viable. It also introduces a node whose execution is a query submission rather than a container. Built-in Ibis nodes are pushed down when their inputs share one warehouse ([D27]({workspace}/decisions/Platform#27)); pushdown targets Postgres and Snowflake ([D25]({workspace}/decisions/Platform#25)).
- **DE 2.2** — Run distributed transforms on Spark, and mid-size transforms on a single node via DuckDB or Polars.
  - *Note:* Ibis on DuckDB runs every built-in node, with Polars by exception ([D27]({workspace}/decisions/Platform#27)). Spark is deferred to a later plugin.
- **DE 2.3** — Join, aggregate, pivot, window, and deduplicate as first-class palette operations. `[cross-discipline]`
- **DE 2.4** — Write idempotently: upsert, merge, and partition-overwrite semantics so a rerun does not double-count.
- **DE 2.5** — Maintain slowly changing dimensions and surrogate keys.
- **DE 2.6** — Handle schema evolution: accept additive and widening changes, detect and halt on breaking ones.
- **DE 2.7** — Correctly reprocess late-arriving and out-of-order records into already-published partitions.
  - *Note:* Expressed through partition dependency functions: a raw partition by ingestion day maps onto a window of event-date partitions ([CORE 3.9](03-capabilities-core.md), [D13]({workspace}/decisions/Platform#13)).
- **DE 2.8** — Process continuous streams rather than bounded batches. `[deferred]`
  - *Note:* Deferred ([D6]({workspace}/decisions/Platform#6)). A different execution model — tasks that never finish, watermarks, checkpointed state. Managed long-running streaming jobs may follow later; a native streaming runtime is out of scope.
- **DE 2.9** — Run a pipeline on a short schedule — every few minutes — over only the data that arrived since the last run.
  - *Note:* Micro-batch, the second step in [D6]({workspace}/decisions/Platform#6). Covers most "near real-time" needs at minute-level latency without a new execution model; builds on DE 1.2 and [CORE 3.3](03-capabilities-core.md).

### 3 · Storage & layout

- **DE 3.1** — Write to open table formats — Iceberg, Delta — with ACID commits and time travel.
  - *Note:* Datasets whose storage target is a lakehouse table are committed by the platform, and the table's own commit follows, made by a publication unit ([D15]({workspace}/decisions/Platform#15), [D55]({workspace}/decisions/Platform#55)); managed datasets on object storage are exposed to external engines through Iceberg metadata projected after each commit ([D42]({workspace}/decisions/Platform#42)); the projection is on by default wherever a catalog is configured and replays every version as its own snapshot ([D44]({workspace}/decisions/Platform#44)).
  - *Note:* Time travel provides dataset versioning at little additional cost, which [CORE 6.1](03-capabilities-core.md) would otherwise have to implement directly.
- **DE 3.2** — Express layered zones (raw, cleaned, curated) as a convention the platform understands and can enforce.
- **DE 3.3** — Declare partitioning and clustering for a target table, and write along those boundaries.
- **DE 3.4** — Compact small files, manage file sizing, and vacuum expired snapshots on a schedule.

### 4 · Quality & reliability

- **DE 4.1** — Declare tests on data — uniqueness, not-null, referential integrity, accepted values, custom assertions — that can fail a run. `[cross-discipline]`
- **DE 4.2** — Monitor dataset freshness and row-volume anomalies against expectation.
  - *Note:* The freshness expectation is declared by the dataset owner, with a default derived from the production schedule where none is given. A breach is reported against the dataset itself, independently of whether a scheduled run occurred ([CORE 6.8](03-capabilities-core.md), DE 5.8). For external sources, freshness is observed by source probes ([D49]({workspace}/decisions/Platform#49)).
- **DE 4.3** — Detect distribution drift on columns between runs. `[cross-discipline]`
- **DE 4.4** — Halt propagation downstream when a quality gate fails, so bad data does not reach consumers. `[shapes the core]`
  - *Note:* Requires the scheduler to distinguish failure from suspension on an upstream quality gate, and to hold rather than retry. Holds are bounded by a configurable timeout, after which the run ends as failed ([D31]({workspace}/decisions/Platform#31)). The attempt whose gate fails ends held, with its staged outputs kept ([D48]({workspace}/decisions/Platform#48)).
- **DE 4.5** — Quarantine rejected records to a dead-letter location and reprocess them once fixed.
- **DE 4.6** — Reconcile source and destination counts or checksums after a load.

### 5 · Governance

- **DE 5.1** — Resolve lineage at column level, not only at task level — what feeds this field, what breaks if it changes. `[shapes the core]`
  - *Note:* Requires parsing transformation logic rather than observing task edges alone. Feasible for SQL nodes and not achievable inside arbitrary code nodes; the boundary is recorded in [D10]({workspace}/decisions/Platform#10): derived for parseable nodes, declared or task-level for custom code.
- **DE 5.2** — Catalog datasets with descriptions, owners, tags, and a business glossary.
- **DE 5.3** — Detect, classify, mask, and tokenize personal data.
- **DE 5.4** — Enforce access control at table, column, and row level.
- **DE 5.5** — Apply retention policies and propagate an erasure request through every derived dataset.
  - *Note:* Tractable only where lineage exists, and the clearest commercial justification for the lineage work.
- **DE 5.6** — Agree a data contract between a producing and a consuming workflow, and fail the producer when it breaks the contract.
- **DE 5.7** — Track lineage and rerun work at partition granularity, not whole-dataset granularity. `[shapes the core]`
  - *Note:* Prevents recomputation of a full year to correct a single day. Depends on [CORE 3.3](03-capabilities-core.md).
- **DE 5.8** — Operate a dataset schema in observed mode, where it is inferred and recorded but not enforced, and promote it to an enforced contract with a declared evolution rule when other pipelines begin consuming it.
  - *Note:* Contract-first declaration would impose ceremony on exploratory work; unenforced schemas would leave production consumers unprotected. The promotion step is the boundary between the two.
- **DE 5.9** — Inherit data classification along lineage, taking the highest sensitivity among a dataset's inputs, and require an explicit, audited assertion by an accountable owner to lower it.
  - *Note:* Classification here denotes sensitivity and handling — a level such as public, internal, confidential or restricted, plus special categories such as PII, PHI, PCI or export-controlled. Declassification after aggregation or anonymization is a judgment, never an automatic consequence of a transformation. Datasets classified restricted or above are not projected into external catalogs unless their owner allows it ([D44]({workspace}/decisions/Platform#44)). A lowered classification arriving through git deploys only when its author holds `dataset.manage` or an authorized principal approves it ([D45]({workspace}/decisions/Platform#45)).
- **DE 5.10** — Extend classification and masking to metadata embedded inside files, such as patient identifiers in DICOM headers, with each dataset family exposing its metadata fields for that purpose.
