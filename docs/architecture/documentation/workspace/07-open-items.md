## Open items

Questions the design anticipates but has not yet resolved. Each becomes a decision or a capability line once settled; a resolved item points to the decision that resolved it.

**Behavior at scale**

### S1 · Retention cost of reproducibility

**Status:** Open

Retaining inputs so that runs remain re-executable is expensive. The mitigation is to reference rather than copy: an Iceberg snapshot identifier or an S3 object version costs nothing to record, whereas a materialized copy incurs storage cost indefinitely. Tier decay ([D7]({workspace}/decisions/Platform#7)) is therefore a statement about the point at which retention ceased to be funded.

- **To settle.** Default retention periods, guidance on when an author should copy a source rather than read it ephemerally ([D35]({workspace}/decisions/Platform#35)), and which budget carries the cost.

### S2 · Verification cost at scale

**Status:** Open

A verification run consumes as much compute as the original run. At scale, verification must be sampled or tiered: compare summary statistics first — row counts, per-column aggregates, key hashes — and perform a full comparison only on request.

- **To settle.** The default verification level, the policy for selecting which runs are verified, and how a partial verdict is represented.

### S3 · Preview and inspection generation

**Status:** Open

Previews and node-level inspection data must be sampled and generated at write time. Computing them on demand over a large artifact makes the interface unusable and the cost unpredictable.

- **To settle.** Sample sizes and sampling method per artifact type, and the retention period for preview data.

### S4 · Scheduler load under large fan-out

**Status:** Resolved · [D43]({workspace}/decisions/Platform#43)

Large fan-out places load on the control plane rather than the data path: 10,000 task runs means 10,000 state records and lease renewals. Batched state transitions, leases and fair queuing are the mechanisms that absorb this.

- **Outcome.** Scale targets, batched state writes, per-agent lease renewal and windowed creation of map task runs. See [D43]({workspace}/decisions/Platform#43).

### S5 · Metadata and log growth

**Status:** Open

Task run tables and log volumes grow without bound. Both require partitioning and archiving, and logs must remain outside the metadata database.

- **To settle.** Archival thresholds and destinations, retention periods per data class, and the query paths that must remain fast against archived history.

### S6 · Data locality and egress

**Status:** Open · deferred ([D26]({workspace}/decisions/Platform#26))

Execution units should be scheduled in the region and availability zone where their data resides. Cross-region reads are slow and, in cloud deployments, chargeable.

- **Deferred.** Placement constraints are deferred from the first release. Location recording, eligibility checks on cache hits and explicit placement by the planner are kept so that they can be introduced without rework ([D26]({workspace}/decisions/Platform#26)).
- **To settle.** Whether placement constraints are first-class in the IR or supplied by the backend abstraction, and how a conflict between placement and available capacity is resolved.

### S7 · Skew and stragglers

**Status:** Open

A single partition an order of magnitude larger than its peers determines the runtime of an entire stage. Per-shard timing and the option to rebalance must be visible to the user.

- **To settle.** Whether rebalancing is automatic or advisory, and what skew diagnostics are surfaced on the canvas and in run history.

### S8 · Out-of-memory escalation

**Status:** Open

When an execution unit is terminated for exceeding its memory allocation, retrying once at a higher memory tier and recording the escalation is preferable to failing the run outright.

- **To settle.** The escalation ladder and its ceiling, whether escalation is enabled by default, and how the escalation is reflected in cost attribution and in the run record.

**Data lifecycle · to settle before the model hardens**

### S9 · Version selection and consistent read sets

**Status:** Resolved · [D14]({workspace}/decisions/Platform#14)

Which version of an input a run reads — the latest at the moment a node starts, the latest when the run starts, or a pinned version — and whether a run reading several datasets sees them all as of the same instant. Without snapshot isolation across inputs, a run can join one day's customers to another day's orders.

- **Outcome.** Versions resolved once at run start under snapshot isolation; pinning per input; coherent reads declared by the user. See [D14]({workspace}/decisions/Platform#14).

### S10 · Atomic publication

**Status:** Resolved · [D15]({workspace}/decisions/Platform#15)

A run that writes several partitions and fails part-way must not leave a partially published version visible, and a retried attempt must never publish twice. This implies staged writes followed by a single commit.

- **Outcome.** Stage, then commit once. The metadata catalog is the commit point for managed datasets; external targets use their own transactions or report partial publication; publication groups are declared by the author. See [D15]({workspace}/decisions/Platform#15).

### S11 · Consumer policy for stale or failed inputs

**Status:** Resolved · [D16]({workspace}/decisions/Platform#16)

When an upstream dataset is stale or its latest publication failed, a consumer may wait, skip its run, or proceed with a warning. Without a declared policy, one late source either silently stalls or silently degrades everything downstream.

- **Outcome.** Per-input policies (wait, proceed, skip, fail, optional) with configurable defaults; degraded outputs cascade downstream with their originating reason. See [D16]({workspace}/decisions/Platform#16).

### S12 · Non-tabular datasets

**Status:** Resolved · [D17]({workspace}/decisions/Platform#17)

Files such as BAM and FASTQ, trained models and feature sets must follow the same lifecycle. For these, schema becomes a format plus metadata, a partition is typically a sample or entity, and comparators and previews differ.

- **Outcome.** Families and first-release scope recorded in [D17]({workspace}/decisions/Platform#17), with the structural capabilities they require.
- **Outcome.** Models are a specialized dataset type ([D17]({workspace}/decisions/Platform#17)).
- **Outcome.** One extension point per family, running in the data plane ([D17]({workspace}/decisions/Platform#17)).

### S13 · Stable identity under rename

**Status:** Resolved · [D19]({workspace}/decisions/Platform#19)

A dataset needs an immutable internal identifier separate from its mutable name, so that renaming it does not break lineage, consumers or history.

- **Outcome.** Fixed names with display titles and an immutable internal identifier; deleted names are not reused ([D19]({workspace}/decisions/Platform#19)).

### S14 · Backfill commit granularity

**Status:** Resolved · [D20]({workspace}/decisions/Platform#20)

A backfill over 31 days may publish 31 snapshots or one. Per-interval commits enlarge version history and trigger repeated downstream reconciliation; a single commit delays all results until the final interval completes.

- **Outcome.** Per-interval commits with coalesced downstream reconciliation; atomic mode for restatements; lower priority than scheduled runs ([D20]({workspace}/decisions/Platform#20)).

**Data lifecycle · may be settled later**

### S15 · Retention defaults and legal holds

**Status:** Open

Default retention per layer, legal holds that suspend deletion, and exemption of pinned versions from garbage collection.

- **To settle.** Per-layer defaults and who may place or lift a hold. Also the default retention of quarantined versions ([D31]({workspace}/decisions/Platform#31)), and the development retention defaults proposed by [D50]({workspace}/decisions/Platform#50).

### S16 · Deprecation and deletion

**Status:** Open

A deprecation notice period, notification of consumers, and blocking of deletion while active consumers remain.

- **To settle.** Notice periods and the override path for urgent deletion.

### S17 · Breaking schema changes

**Status:** Open

Whether a breaking change rewrites history or publishes a parallel major version of the dataset while consumers migrate.

- **To settle.** The default strategy and how long parallel versions are maintained.

### S18 · Overriding a failed quality gate

**Status:** Resolved · [D45]({workspace}/decisions/Platform#45)

Who may release a quarantined version into use, under what conditions, and with what audit trail.

- **Outcome.** The dataset's owner or a Maintainer of its project, configurable per dataset; every release is audited and does not expire. The override mechanics are recorded in [D31]({workspace}/decisions/Platform#31). See [D45]({workspace}/decisions/Platform#45).

### S19 · Access control and visibility

**Status:** Open

Whether a user without read access to a dataset may still see that it exists, and see it in lineage.

- **To settle.** Visibility rules for catalog entries, lineage nodes and previews. The default is recorded in [D30]({workspace}/decisions/Platform#30): unreadable entities are hidden.

### S20 · Sharing across projects and tenants

**Status:** Open

Read-only sharing of a dataset with another project and, in the cloud edition, with another tenant.

- **To settle.** The sharing model, its interaction with cache scope ([D9]({workspace}/decisions/Platform#9)), and revocation.

### S21 · Lineage interoperability

**Status:** Open

Export of lineage in the OpenLineage format so that external catalogs such as DataHub, Unity Catalog or Glue can consume it.

- **To settle.** Export only, or import as well, and at what granularity.

### S22 · Cost attribution per dataset

**Status:** Open

Attribution of storage and of the compute that produces a dataset, to support decisions about retention and refresh frequency.

- **To settle.** The attribution method for shared upstream work.

### S23 · Data residency

**Status:** Open · deferred ([D26]({workspace}/decisions/Platform#26))

A declared region on a dataset, constraining where it is stored and where the units that read it may run.

- **Deferred.** Residency rules are deferred with placement constraints ([D26]({workspace}/decisions/Platform#26)). Because every attempt and artifact records its location, data stored and processed before enforcement can still be judged against a residency rule introduced later.
- **To settle.** Enforcement at storage, at placement, or both.

**Authoring and execution**

### S24 · Dynamic output schemas

**Status:** Resolved · [D41]({workspace}/decisions/Platform#41)

Nodes whose output columns depend on the data — a pivot or one-hot encoding over values not known in advance — break design-time schema propagation through the IR, on which validation, the canvas, contracts and column-level lineage all rely.

- **Outcome.** Static, derived and dynamic output-schema modes; dynamic nodes may declare expected columns, otherwise downstream schemas are pending until a sample run; contracts are checked at publication and authoring never refuses. See [D41]({workspace}/decisions/Platform#41).

### S26 · Plugin identity and distribution

**Status:** Open

Third-party plugins provide node types, format types and their implementations ([D18]({workspace}/decisions/Platform#18), [CORE 1.9](03-capabilities-core.md)), and tools may add keys of their own to IR documents. Both need names that cannot collide with one another or with the platform's own. The names the IR specification and the platform define never contain `.` or `/` ([D56]({workspace}/decisions/Platform#56)), so names qualified by a publisher can be added without colliding with them.

- **To settle.** Publishers and packages, such as a publisher account unique within a registry and packages named after it. A public registry, private registries per installation, and mirrors for installations without internet access ([D22]({workspace}/decisions/Platform#22)). Uniqueness of publishers across registries used by one installation. Publisher verification and package signing. How a package version relates to node-type versions and image digests ([D18]({workspace}/decisions/Platform#18), [D41]({workspace}/decisions/Platform#41)). Where the registry protocol and a hosted registry fall relative to the open-core line ([D53]({workspace}/decisions/Platform#53)). What a package may declare, including keys added to IR documents and the namespaced annotations on ports ([D41]({workspace}/decisions/Platform#41)).

### S27 · Name of the loop scope in expressions

**Status:** Open

Expressions inside a loop may reference `loop.index`, `loop.carried.<name>` and the current iteration's value outputs ([D41]({workspace}/decisions/Platform#41), [D46]({workspace}/decisions/Platform#46)). `loop` is a reserved word in CEL, and cel-go 0.32.0 rejects it as a variable name, so such expressions cannot compile as decided.

- **To settle.** A root name for the loop scope that CEL accepts, such as `iteration`, settled with the expression environment of the IR specification, with [D41]({workspace}/decisions/Platform#41) and [D46]({workspace}/decisions/Platform#46) amended in place.

**Deployment**

### S25 · Single-machine object storage

**Status:** Open

Self-hosted distributions bundle an S3-compatible store as the default storage target for installations without object storage of their own, so that casual users need not provide one. Any S3-compatible or cloud object storage can be configured instead ([D4]({workspace}/decisions/Platform#4)). A bundled S3-compatible store, rather than the local filesystem, keeps one storage path in every deployment: browser uploads through pre-signed URLs ([D4]({workspace}/decisions/Platform#4), [D21]({workspace}/decisions/Platform#21)), credentials scoped by the agent ([D40]({workspace}/decisions/Platform#40)) and external readability of projected tables ([D44]({workspace}/decisions/Platform#44)).

- **To settle.** The product: SeaweedFS (Apache-2.0), Garage (AGPLv3) and RustFS (Apache-2.0, version 1.0 in September 2026) are candidates; MinIO's community edition was archived upstream in February 2026. Scoped short-lived credentials on the chosen store ([D40]({workspace}/decisions/Platform#40)). License compatibility, reviewed with the license ([D5]({workspace}/decisions/Platform#5)). Moving existing datasets from the bundled store to another storage target. Consistent backup of the store together with Postgres.
