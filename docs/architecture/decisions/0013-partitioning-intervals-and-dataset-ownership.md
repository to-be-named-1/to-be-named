# 13. Partitioning, intervals and dataset ownership

Date: 2026-10-11
Applies to: platform.controlPlane, datasetOwner, workflowAuthor

## Status

Accepted

Amended by [35. Ephemeral extraction](0035-ephemeral-extraction.md)
Amended by [44. Minimum technology stack](0044-minimum-technology-stack.md)
Amended by [51. Adoption of existing data](0051-adoption-of-existing-data.md)

## Decision

Partition granularity and logical intervals are user decisions; the platform applies and validates them but never chooses them. Each dataset has exactly one producer. Datasets copied from mutable sources are partitioned by ingestion time at the raw layer and by event time downstream, connected by declared partition dependency functions; whether a source is copied is the author's explicit choice ([D35](0035-ephemeral-extraction.md)).

- **Ownership.** Partition granularity — daily, hourly, by region, by tenant or none — is a property of the **dataset**, set by its owner. The logical interval — for example “hourly, covering the previous hour” — is a property of a workflow's **schedule**, set by its author.
- **Validation.** The platform checks that interval and partitioning are compatible. An interval equal to or coarser than the partition is accepted. An interval finer than the partition requires the author to declare the partition **open** — appended to by successive runs until explicitly marked complete — so that consumers never mistake a partial partition for a finished one. Boundaries that cannot align are rejected.
- **Timezone.** Timezone is part of both the partition scheme and the interval declaration. A daily partition in UTC and one in Africa/Cairo are different partitions, and a mismatch is rejected rather than silently shifted.
- **Single producer.** Exactly one node in one workflow publishes to a dataset; any number may consume it. Several sources feeding one dataset are combined by a single node. This keeps publication free of races, lineage unambiguous and contract ownership clear, and makes datasets the interfaces between workflows.
- **Adoption.** Existing folders are mapped to partitions by a path template whose time zone and granularity equal the dataset's; adopted partitions are complete except the newest, which the owner confirms; and switchover is the act by which a node becomes an adopted dataset's single producer ([D51](0051-adoption-of-existing-data.md)).
- **Time axes.** A dataset extracted from a mutable source is partitioned by **ingestion time**: the raw partition is the only faithful snapshot of what the source held, so downstream reruns read the raw partition and never re-query the source; amended by [D35](0035-ephemeral-extraction.md), this applies to copied sources, and an ephemeral source is re-read at run time. Re-extraction is an explicit act that produces a new version of the raw partition. Curated datasets are partitioned by **event time**, because that is how consumers query them, with a declared lateness window. Amended by [D44](0044-minimum-technology-stack.md): the ingestion time is written as a column of the raw dataset, since partition keys are stored as columns.
- **Dependencies.** A node declares how its output partitions depend on its input partitions: identity (the default), a time window such as “the same day to three days later”, all available partitions, the latest partition, or specific values. Where a declared window is too coarse, a merge node may instead discover the affected partitions from the data at run time, at the cost of not knowing the plan in advance.
- **Platform role.** The platform proposes defaults at creation, which the owner confirms — a daily schedule suggests daily partitions, a small dimension table suggests none — and may later advise on granularity from observed partition sizes. It decides physical layout (file sizing, compaction, clustering), which affects performance but not the logical model.
- **Change.** Changing a partitioning scheme is a migration performed by the owner: it produces a new version of the scheme, rewrites history, and requires every downstream dependency mapping to be revalidated. It is never a silent setting change, which is why the default proposed at creation matters.
