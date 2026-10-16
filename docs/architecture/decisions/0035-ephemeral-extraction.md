# 35. Ephemeral extraction

Date: 2026-10-11
Applies to: platform.controlPlane, platform.unitRuntime, dataSources, workflowAuthor

## Status

Accepted

Amends [4. Datasets as first-class objects](0004-datasets-as-first-class-objects.md)
Amends [13. Partitioning, intervals and dataset ownership](0013-partitioning-intervals-and-dataset-ownership.md)
Amended by [49. Source probes](0049-source-probes.md)

## Context

**Ephemeral extraction** (D35). Requiring every unversionable source to be copied was rejected: not every team needs reproducibility, and copying terabytes into the customer's own storage is a cost the platform should not impose. Storage is an explicit choice and versioning a property of the source; an ephemeral read of a versioned source loses nothing, and an ephemeral read of an unversioned source keeps complete provenance and read positions, losing only re-execution, verification and caching.

As first recorded, the decision presented referenced-by-version, copied and ephemeral as three exclusive modes and left the default open; version and storage are independent, and the storage choice is always explicit.

## Decision

No source is copied unless its author chooses to copy it. A read from an external source may be **ephemeral**: performed at run time, with nothing stored unless a downstream output is, and fusable into the transformations that follow. Not every team needs reproducibility, and copying terabytes into the customer's storage because a source is unversionable is not a cost the platform imposes ([D36](0036-data-engineering-practice-first-reproducibility-by-choice.md)).

- **Two independent properties.** How a source read is handled is set by two properties that combine freely:
  - **Storage**, chosen explicitly by the author for every external source: **ephemeral** (read at run time, nothing stored, fusable) or **copied** into a raw managed dataset ([D4](0004-datasets-as-first-class-objects.md), [D13](0013-partitioning-intervals-and-dataset-ownership.md)) with configurable retention. There is no default; the set-up shows the consequences of each choice.
  - **Version**, a property of the source rather than a choice: where the source can identify what was read — an Iceberg snapshot, an object version, an immutable logical interval — the platform records that version on every read, whatever the storage choice.
- **Combinations.** An ephemeral read of a versioned source stays eligible for re-execution and verification for as long as the source retains that version (for example until an Iceberg snapshot expires), and is cacheable. An ephemeral read of an unversioned source caps the run at Traceable ([D7](0007-reproducibility-guarantee.md)): re-executing it as recorded and verifying it are unavailable, leaving only running again on current data (CORE 2.16), and it is not cacheable unless a time-to-live is set (CORE 2.13). A copied read is eligible for re-execution for as long as the copy is retained, whether or not the source is versioned; copying a versioned source protects against the source expiring its versions.
- **Amends.** [D4](0004-datasets-as-first-class-objects.md): an unversionable source is no longer copied by default, and reference without copying becomes the ephemeral storage choice, which may be fused. The fusion conditions in the [vocabulary]({workspace}/documentation#2): the output of an external-source read must be stored only when its source is copied. [D13](0013-partitioning-intervals-and-dataset-ownership.md): the rule that downstream reruns read the raw partition rather than re-query the source applies to copied sources.
- **Still recorded.** Every read records its provenance, the source version where one exists, and the range of positions consumed where the extraction strategy provides one, so lineage stays complete and incremental cursors work under either storage choice (DE 1.2).
- **Deletes.** Detecting hard deletes by comparing snapshots needs the previous snapshot's keys; for an ephemeral read of an unversioned source this is available only if a compact key set is retained per run.
- **Where copies live.** Under bring-your-own-compute, a copy is written to the customer's own storage target ([D4](0004-datasets-as-first-class-objects.md), [D22](0022-deployment-topologies.md)), never to vendor infrastructure; only the fully managed topology stores it with the vendor. The cost an ephemeral read avoids is therefore the customer's own storage.
- **Probed versions.** Amended by [D49](0049-source-probes.md): where a source can be read as of a probed position, its version is fixed at run start by a source probe rather than discovered when a unit reads, so every read in the run uses the same version and nodes reading it are cacheable before the run.
