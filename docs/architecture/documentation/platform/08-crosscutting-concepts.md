## Crosscutting concepts

### Processing engines in practice

Two worked examples showing how the planner applies [D25]({workspace}/decisions/Platform#25) to [D28]({workspace}/decisions/Platform#28) under the bring-your-own-compute model ([D22]({workspace}/decisions/Platform#22)): where each unit runs, what data moves, and why. Figures are indicative.

#### Retail · warehouse and file data

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
| U2 | Snowflake query, then Ibis on DuckDB | Only 3 of 14 customer columns are extracted after pushdown. Sessionization by inactivity gap is expressible with window functions, so under Ibis first ([D27]({workspace}/decisions/Platform#27)) it chains with the join and aggregation into one DuckDB segment. |
| U3 | Python | A training code node, reading the published feature table. |

| Variation | Effect on the plan |
|---|---|
| A · mapping stored in Snowflake | The owner gives `ref.store_regions` Snowflake as its storage target. U1 becomes a single pushed-down query, nothing is extracted, and the result is written inside Snowflake. |
| B · extraction over the cap | If the reduced orders data exceeds the configured extraction cap, the plan stops and asks the author instead of proceeding, and repeats the suggestion of variation A ([D25]({workspace}/decisions/Platform#25)). |
| C · 2 TB of events per day | The partition fails the planner's capacity check ([D34]({workspace}/decisions/Platform#34)). Sessionization groups by customer while the data is partitioned by day, so the planner inserts a repartition step: about 256 buckets of 8 GB by customer, with U2 fanned out per bucket and the extracted customer columns read by every bucket ([CORE 2.26]({workspace}/documentation#3)). |

A variation in which `raw.customers` may not leave Snowflake applies only once placement constraints are introduced ([D26]({workspace}/decisions/Platform#26)).

#### Genomics · non-tabular data

A research group aligns and calls variants for 40 sequencing samples on its own HPC cluster, then joins the results with a small clinical spreadsheet and produces a report. Nothing in the flow touches a warehouse.

> *Diagram: Genomics flow: FASTQ files are read in place and aligned, variant-called and converted by containers on the customer's HPC cluster, fanned out by sample and by genomic region; the Parquet results are joined with an uploaded clinical file on DuckDB and reported in Python on the customer's Kubernetes cluster.*
>
> **Genomics plan.** One workflow, three runtimes (container commands, Ibis on DuckDB, Python) and three ways of parallelizing: by item (40 samples), by split within an item (24 regions read through the BAM index), and a single unit for the join and report. Each unit's backend is chosen separately, all of it on customer infrastructure.

| Step | Runtime and backend | Parallelism and reason |
|---|---|---|
| Align | BWA container command, HPC agent | Fan-out by item: one unit per sample. The FASTQ files are registered in place rather than uploaded ([D4]({workspace}/decisions/Platform#4)). |
| Call variants | GATK container command, HPC agent | Fan-out by split: the genomics family plugin reports splits through the BAM index, giving 24 regions per sample ([CORE 6.19]({workspace}/documentation#3)). BAM and index travel together as one file group ([CORE 6.16]({workspace}/documentation#3)). |
| Convert | bcftools container command, HPC agent | Fan-out by item, producing Parquet so that the next step can treat the variants as tabular data. |
| Join | Ibis on DuckDB, Kubernetes | Both inputs are files on object storage, so the join runs in-process ([D25]({workspace}/decisions/Platform#25), [D27]({workspace}/decisions/Platform#27)). |
| Report | Python, Kubernetes | A single unit producing the summary report. |

### Dataset lifecycle

What it means in practice for datasets to be first-class objects rather than the outputs of runs: the properties a dataset carries, how versions are published, how state is tracked per partition, and what becomes possible once the platform reasons about data rather than about pipeline invocations. The section elaborates [D4]({workspace}/decisions/Platform#4) and the data-lifecycle decisions [D13]({workspace}/decisions/Platform#13) to [D16]({workspace}/decisions/Platform#16), [D19]({workspace}/decisions/Platform#19), [D20]({workspace}/decisions/Platform#20) and [D24]({workspace}/decisions/Platform#24). Figures are numbered within the section.

#### 1 · What a dataset carries

A dataset is an aggregate with its own identity and lifecycle. The distinction from an artifact is the whole point: an **artifact** is a run-scoped output, often temporary; a **dataset version** is a published asset with an owner, a contract and consumers. Every dataset version is an artifact or a reference; most artifacts never become dataset versions.

> *Diagram: A dataset object with identity, schema, policy and state on the left, its ordered versions in the center, and each version's materialization on the right.*
>
> **Figure 1.** **Anatomy.** The dataset carries identity, schema and policy that outlive any run. Each version is one materialization, and a version is either **managed** (bytes in the platform's artifact store) or **external** (a reference to data the platform does not own). Both are the same kind of object; only the pointer differs.

- **Identity.** A stable name, owner, description and tags that survive the deletion of any pipeline that writes to it.
- **Schema and contract.** Columns, types and keys, with an evolution rule enforced at publication. Producers are validated; consumers are guaranteed compatibility.
- **Versions.** An ordered sequence of materializations. Each records its producing run, the input positions consumed, its statistics and its state.
- **Partitions.** Addressable subdivisions of a version, each with independent state, lineage and rerun.
- **Materialization policy.** Managed (written, versioned and retained by the platform, on its storage or the customer's, [D4]({workspace}/decisions/Platform#4)) or external (a reference to a warehouse table or bucket the platform does not own).
- **Declared reads and writes.** Nodes declare the datasets they consume and produce; lineage and permissions follow from those declarations.
- **Freshness expectation.** A stated currency requirement, which makes staleness measurable independently of whether a schedule ran.
- **Classification and retention.** Data classification, retention period and erasure obligations, propagated to derived datasets along lineage.
- **Consumers.** The set of pipelines, datasets and models that read it — the basis for impact analysis before a change or deletion.

#### 2 · Publication

Publication is the moment an artifact becomes part of a dataset's history. It is also the enforcement point for the contract, which is what allows a consumer to depend on a dataset rather than on the pipeline that happens to write it. The binding is declared once — a node's output is bound to a named dataset — and every subsequent run of that node publishes automatically; publication is not a manual step performed per run.

- **Declared binding.** The normal case. An output port is bound to a dataset in the node configuration and in the text definition. Each run publishes a new version of the partitions it wrote.
- **Gated publication.** For sensitive or heavily consumed datasets, a version becomes current only after a passing quality gate or an approval, using the same externally resumed execution state as an approval step.
- **Manual promotion.** An artifact from an exploratory run is promoted into a dataset after the fact, which is how a useful one-off becomes a maintained asset.
- **Unbound outputs.** Everything else remains a run-scoped artifact: subject to retention, absent from the catalog, and never a dependency for another pipeline.

> *Diagram: A task run produces an artifact, which is validated against the dataset's contract and either becomes a new version or is refused.*
>
> **Figure 2.** **Publication.** An artifact is a run-scoped output; a dataset version is a published asset. Publication validates the artifact against the dataset's schema contract, assigns the next version, records lineage and notifies consumers. A breaking change fails the producer rather than corrupting the consumer.

#### 3 · Versions and partitions

State lives at the partition level. This is what separates a dataset model from a folder of files, and it is what makes backfills, partial reruns and incremental caching expressible. Partitions and versions are independent axes and are easily confused: a partition is *which slice* of the data, a version is *state over time*. Partitions are not sub-versions, and versions are not created only by structural change — a routine daily run that adds one day of data produces a new version with an unchanged schema.

> *Diagram: A grid of dataset partitions by date, each marked available, stale, not yet materialized or failed, with staleness propagating downstream.*
>
> **Figure 3.** **Partitions.** State is tracked per partition, not per dataset. A change to one upstream partition marks exactly the downstream partitions that depend on it, which is what makes partition-level rerun and backfill possible without recomputing history.

> *Diagram: A grid with partitions across and snapshots down, showing that each publication creates a snapshot which reuses unchanged partition versions and points at newly written ones.*
>
> **Figure 4.** **Two axes.** A **partition** is a slice of the key space, fixed by the partitioning scheme. A **version** is state over time. Every successful publication creates a new snapshot, whether or not anything structural changed; the snapshot reuses the partition versions it did not touch. Schema evolution is a third, separate property recorded on the version.

> *Diagram: States of a dataset version: declared, materializing, available, superseded, expired, with a quarantined branch when a quality gate fails.*
>
> **Figure 5.** **Version states.** Versions are immutable once available; a correction produces a new version rather than editing an old one. Superseded versions stay readable so that historical runs remain re-executable until retention removes them — the point at which affected runs decay to Traceable. A quarantined version may later be released by an override ([D31]({workspace}/decisions/Platform#31)).

#### 4 · Contract and expectation

Both the schema contract and the freshness expectation are declared by the dataset owner, with inference used to avoid imposing ceremony on exploratory work.

- **Observed schema.** Default for a new dataset. The schema is inferred at first publication and recorded; changes are logged but not enforced.
- **Enforced contract.** Promoted by the owner, normally when another pipeline begins consuming the dataset. The owner selects an evolution rule — additive only, widening permitted, or breaking changes requiring a major version — and publications are validated against it.
- **Freshness expectation.** An optional declared target and maximum lateness. Where none is declared, a default is derived from the production schedule. Breaches raise alerts and mark the dataset stale in the catalog, independently of whether a scheduled run occurred.
- **Where it is defined.** In the interface and in the text definition, since dataset declarations round-trip to version control with the rest of the pipeline definition. A change to the contract, classification or retention needs the owner's permission wherever it is made ([D45]({workspace}/decisions/Platform#45)).

#### 5 · Lineage

Because reads and writes are declared, the lineage graph is derived rather than maintained by hand, and it records position ranges rather than only identities.

> *Diagram: Lineage alternating between datasets and runs, with reads and writes labeled, and a second row showing column-level lineage limited to declarative nodes.*
>
> **Figure 6.** **Lineage.** Because nodes declare what they read and write, lineage is derived rather than documented. Reads record the range of positions consumed, so the graph answers both “what produced this” and “what must change if this changes”. Column-level detail is available where transformation logic can be parsed.

#### 6 · Reconciliation

The behavioral consequence of the model: the platform can be asked for a state of the data rather than for the execution of a pipeline.

> *Diagram: A request for a dataset to be current is compared against observed partition state, producing a minimal plan that is dispatched and fed back into observed state.*
>
> **Figure 7.** **Asset-based scheduling.** Making datasets first-class allows a second entry point: instead of invoking a pipeline, a request states the data that should exist. The reconciler derives the minimum work required. Data-triggered scheduling, cross-workflow dependencies and partition-level rerun become the same mechanism.

#### 7 · Governance

Classification, retention and erasure are properties of the asset, so they travel with it. **Classification** here means data sensitivity and handling, not statistical classification: a sensitivity level (public, internal, confidential, restricted) and any special categories that apply (PII, PHI, PCI, export-controlled). It drives masking, access control, retention, residency and erasure obligations.

- **Declared by the owner.** Optionally assisted by automated detection, which proposes candidate classifications for confirmation rather than applying them silently.
- **Inherited along lineage.** A derived dataset takes the highest sensitivity among its inputs by default.
- **Declassification is explicit.** Aggregation or anonymization may genuinely reduce sensitivity, but only an auditable assertion by an accountable owner may lower a classification. It is never an automatic consequence of a transformation.

> *Diagram: An erasure request entering at the raw dataset and cascading through derived datasets to a model flagged for retraining.*
>
> **Figure 8.** **Governance.** A dataset's classification is a property of the asset, so it propagates to everything derived from it. An erasure obligation follows the same edges, which is only tractable because lineage is derived automatically.

#### 8 · End-to-end walkthrough

One dataset, from declaration to deletion, with the figure that illustrates each stage.

1. **Declaration.** The dataset is registered before any data exists: name, owner, schema contract, classification, retention and freshness expectation. A pipeline may reference it as an output while it is still empty. *(Fig 1)*
2. **First materialization.** A run produces an artifact. Publication validates it against the contract, assigns version 1 and records which input positions were consumed. *(Fig 2)*
3. **Incremental updates.** Subsequent runs add or replace partitions. Each publication produces a new snapshot that reuses untouched partition versions; the previous snapshot remains readable and is marked superseded. *(Fig 3, 4, 5)*
4. **Consumption.** Downstream nodes declare the dataset as an input. Lineage is derived from those declarations, and access is enforced against the dataset rather than a storage path. *(Fig 6)*
5. **Staleness.** A change to an upstream partition marks the dependent downstream partitions stale. Freshness is evaluated against the dataset's SLA, not against a schedule having run. *(Fig 3)*
6. **Reconciliation.** A request for the dataset to be current yields a minimal plan: only stale or missing partitions, and only the upstream work they require. *(Fig 7)*
7. **Schema change.** An additive change publishes normally. A breaking change is refused at publication and reported to the producer, leaving consumers on the last valid version. *(Fig 2)*
8. **Governance events.** Classification propagates to derived datasets. An erasure request cascades along the same lineage edges, rewriting, rebuilding and flagging as it goes. *(Fig 8)*
9. **Retention and decay.** Versions expire under the retention policy. Runs whose inputs have expired lose the ability to be re-executed and are reported as Traceable rather than silently unverifiable. *(Fig 5)*
10. **Deprecation.** The dataset is marked deprecated while consumers migrate, then deleted. Consumer lists make the blast radius explicit before deletion occurs.

The model shown here assumes [D4]({workspace}/decisions/Platform#4) (datasets as first-class objects) and the seams recorded in [D12]({workspace}/decisions/Platform#12). Asset-based reconciliation (Figure 7) is recorded in [D24]({workspace}/decisions/Platform#24), within a single project.

### IR

Every definition a project holds, its workflows, layouts, datasets, environments and project settings, is an IR document: a YAML file whose values follow JSON's data model, committed to git in git-connected projects and held by the platform otherwise ([D3]({workspace}/decisions/Platform#3), [D41]({workspace}/decisions/Platform#41)). Each document states its kind and its IR version, and names its nodes by readable keys that keep their identity across renames ([D56]({workspace}/decisions/Platform#56)). The compiler in the control plane checks every document against the YAML subset, the schema of its IR version and its semantic rules before compiling it ([D47]({workspace}/decisions/Platform#47)).

The normative detail is the IR specification, `docs/ir/` in the repository, which this documentation does not render; its schema and conformance corpus are in `controlplane/internal/authoring/ir/`.
