## Solution strategy

### Key choices

1. **One intermediate representation is the single source of truth** ([D3]({workspace}/decisions/Platform#3), [D41]({workspace}/decisions/Platform#41)). The canvas, the YAML text form in git and imported templates are views of it; validation, cache keys, provenance and reproducibility checks operate on it. For a git-connected project, git is authoritative and the platform deploys from it ([D45]({workspace}/decisions/Platform#45)).
2. **Four planes, divided by responsibility and trust** ([D21]({workspace}/decisions/Platform#21)), described below.
3. **A pull-based agent in every deployment** ([D29]({workspace}/decisions/Platform#29), [D40]({workspace}/decisions/Platform#40)). Topologies differ only in where the control plane runs; the agent is the single egress of the data plane, where credentials are minted and secrets resolved.
4. **A leader-centered control plane with its invariants in the database** ([D47]({workspace}/decisions/Platform#47)). One binary runs on every replica, deployed in roles; a single active leader holds queues, fair share and lease renewals in memory, fenced by an epoch; Postgres is the only stateful dependency.
5. **Datasets as first-class objects, made current by one commit** ([D4]({workspace}/decisions/Platform#4), [D15]({workspace}/decisions/Platform#15), [D42]({workspace}/decisions/Platform#42)). An attempt stages its outputs; the control plane makes them current in one database transaction, which is the commit point.
6. **Fine-grained nodes, fused automatically into units** ([D32]({workspace}/decisions/Platform#32), [D33]({workspace}/decisions/Platform#33)). Engines are chosen by where the data lives ([D25]({workspace}/decisions/Platform#25)); built-in nodes are Ibis expressions on DuckDB ([D27]({workspace}/decisions/Platform#27)).
7. **Cache keys chained through nodes** ([D8]({workspace}/decisions/Platform#8)): input-addressed for every node, with content-addressed early cutoff where outputs are small.
8. **Isolation enforced from the start** ([D30]({workspace}/decisions/Platform#30), [D45]({workspace}/decisions/Platform#45)): row-level security on the tenant, and a mandatory authorization layer for projects, roles and clearance.
9. **Domain-driven design** ([D54]({workspace}/decisions/Platform#54)). The control plane is divided into bounded contexts, each owning its schema and package tree, whose aggregates enforce their invariants in the database; contexts integrate through interfaces and domain events, and anti-corruption layers translate external models at the edges.

### Architecture planes

The platform is divided into four planes by responsibility and trust ([D21]({workspace}/decisions/Platform#21)). Storage systems belong to planes rather than forming planes of their own.

- **Interface.** Web application, API, CLI and git synchronization. Authenticates people, turns their actions into definition changes or commands, and presents state. Holds no state of its own; scales with users.
- **Control.** Compiler, planner, run driver, reconciler, scheduler, dispatcher, catalog, cache index, provenance, policy and plugin registry ([D47]({workspace}/decisions/Platform#47)). The single source of truth for what exists and what has happened, held in Postgres. Scales with tasks, partitions and datasets, not data volume.
- **Data.** Execution units in containers on a backend. The unit runtime resolves inputs, runs fused nodes, calls format plugins, stages outputs and requests commits. Holds no state beyond a unit's life; scales with data and compute; sandboxed.
- **Observability.** Live log tail, log archive, metrics time series, node events and alerts. High-volume and append-only, stored outside the metadata database; redacts secrets on ingestion.

The planes keep four invariants:

- **Bulk data.** Never passes through the interface or control planes. They handle pointers, statistics and pre-computed previews only.
- **Untrusted code.** Runs only in the data plane. The control plane executes platform code exclusively.
- **Disposability.** Any data-plane component can be terminated at any moment. Leases expire, units are retried, and fencing prevents a superseded attempt from committing.
- **Correctness.** Never depends on observability. Telemetry may be delayed or lost; state may not.

### Technology

| Area | Choice | Status |
|---|---|---|
| Control-plane store | Postgres, version 17 or later ([D42]({workspace}/decisions/Platform#42), [D44]({workspace}/decisions/Platform#44)) | Chosen |
| Control plane and agent | Go ([D44]({workspace}/decisions/Platform#44)) | Chosen |
| Unit runtime | Python, one CPython version per base image ([D27]({workspace}/decisions/Platform#27), [D44]({workspace}/decisions/Platform#44)) | Chosen |
| Schema migrations | goose: plain SQL embedded in the binary, forward-only, expand then contract ([D44]({workspace}/decisions/Platform#44)) | Chosen |
| Data access | sqlc with pgx v5; every query in a tenant-scoped transaction ([D45]({workspace}/decisions/Platform#45)) | Chosen |
| Isolation and authorization | Postgres row-level security on the tenant; project scope, fixed roles and clearance in a mandatory authorization layer ([D30]({workspace}/decisions/Platform#30), [D45]({workspace}/decisions/Platform#45)) | Chosen |
| Interfaces and protocol | Protobuf with ConnectRPC for the interface, CLI, agent and agent–unit contract; agent transport by unary calls and one long-poll per replica over HTTPS; `buf breaking` in CI; a REST surface through Vanguard later ([D44]({workspace}/decisions/Platform#44)) | Chosen |
| Agent identity | Enrolled key, proven by HTTP Message Signatures (RFC 9421) on every request and response ([D40]({workspace}/decisions/Platform#40), [D44]({workspace}/decisions/Platform#44)) | Chosen |
| Artifact store | Object storage, pluggable; customer storage targets supported ([D4]({workspace}/decisions/Platform#4)) | Chosen |
| Managed tabular format | Parquet, with column statistics and partition keys stored as columns ([D44]({workspace}/decisions/Platform#44)) | Chosen |
| Execution backends | Kubernetes; HPC/Slurm via outbound agents (images commonly run with Apptainer); cloud batch; single-machine container deployment. The first slice uses the single-machine deployment and Kubernetes, driven by a pull-based agent ([D29]({workspace}/decisions/Platform#29)) | Chosen |
| In-process engines | DuckDB through Ibis for every built-in node (spills to disk); Polars for code nodes and justified exceptions; exchanging Arrow | Chosen |
| Relational node definitions | Ibis, compiling through SQLGlot | Chosen subject to the [D27]({workspace}/decisions/Platform#27) spike |
| Warehouses (v1) | Postgres and Snowflake | Chosen |
| Table formats | Iceberg and Delta, used as the commit mechanism underneath where applicable; Iceberg metadata projected for managed datasets on object storage, from the first slice ([D42]({workspace}/decisions/Platform#42)), by PyIceberg in a maintenance unit into REST and SQL catalogs ([D44]({workspace}/decisions/Platform#44)) | Chosen |
| Later engines | Spark, Flink, Ray, all against customer-operated clusters | Deferred |
| Standards | OpenLineage ([S21]({workspace}/documentation#3)), EDAM format ontology ([D18]({workspace}/decisions/Platform#18)) | Candidates |
| IR text form | Strict YAML subset, round-tripping with the canvas, parsed with goccy/go-yaml; comments not preserved on write-back in the first slice; Python SDK generating IR later ([D41]({workspace}/decisions/Platform#41), [D44]({workspace}/decisions/Platform#44)) | Chosen |
| Version control | Git for connected projects, which holds history and review; drafts, and linear platform-held versions for projects without git; deployment by the platform ([D41]({workspace}/decisions/Platform#41), [D45]({workspace}/decisions/Platform#45)) | Chosen |
| Expression language | CEL for conditions, collections, loop termination and parameters ([D41]({workspace}/decisions/Platform#41)), evaluated with cel-go ([D44]({workspace}/decisions/Platform#44)) | Chosen |
| Frontend | React and TypeScript, a Vite single-page application served by the control plane ([D44]({workspace}/decisions/Platform#44)) | Chosen |
| Canvas | React Flow 12, with ELK for automatic layout ([D44]({workspace}/decisions/Platform#44)) | Chosen |
| Leader election | A session-level Postgres advisory lock held by the leader, with an epoch checked by every leader-only write ([D47]({workspace}/decisions/Platform#47)) | Chosen |
| Event delivery | A transactional outbox in Postgres with one row per event and handler, claimed with `FOR UPDATE SKIP LOCKED` and built in-house; NOTIFY only as a hint sent outside transactions ([D42]({workspace}/decisions/Platform#42), [D48]({workspace}/decisions/Platform#48)) | Chosen |
| Stateful dependencies | Postgres only; no cache or message broker in the control plane ([D47]({workspace}/decisions/Platform#47)) | Chosen |
| Module boundaries | One Postgres schema and one Go package tree per bounded context, with import rules checked by depguard in golangci-lint ([D47]({workspace}/decisions/Platform#47)) | Chosen |
| Not yet chosen | Authentication and identity stack, observability stack, image builder and registry tooling | Undecided |
