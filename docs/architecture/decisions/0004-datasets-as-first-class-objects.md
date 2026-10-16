# 4. Datasets as first-class objects

Date: 2026-10-11
Applies to: platform.webApp, platform.cli, platform.controlPlane, platform.bundledObjectStorage, objectStorage, dataSources, datasetOwner

## Status

Accepted

Amended by [35. Ephemeral extraction](0035-ephemeral-extraction.md)
Amended by [44. Minimum technology stack](0044-minimum-technology-stack.md)
Amended by [51. Adoption of existing data](0051-adoption-of-existing-data.md)

## Context

**Uploads are ordinary managed datasets** (D4). No special path is needed; the engine rules treat them as file data.

The reasoning on Snowflake as the single second warehouse for v1, in [D25](0025-processing-engines-and-runtimes.md), also cites this decision.

## Decision

Datasets are domain objects with their own identity, versions, partitions, schema and owner, independent of the runs that produce them.

- **Follows.** Dataset and artifact are distinct terms (see the [vocabulary]({workspace}/documentation#2)).
- **Managed or external.** Decided by who owns the data's lifecycle, not by where the bytes sit. A **managed** dataset is written, versioned, committed and retained by the platform. An **external** dataset is written by someone else; the platform only references it.
- **External sources.** A versionable source — an Iceberg snapshot, an S3 object version — is referenced and its version recorded. An unversionable source is copied into a raw dataset at ingestion by default (DE 1.7). Its owner may instead declare **reference without copying**, accepting that runs reading it are capped at Traceable. Amended by [D35](0035-ephemeral-extraction.md): nothing is copied by default; for every external source the author chooses explicitly between an ephemeral read, which stores nothing and may be fused into downstream transformations, and a copy, while the source's version, where it has one, is recorded either way.
- **Storage targets.** A managed dataset may live on platform storage or on the customer's own: object storage in their account, a table registered in their lakehouse catalog, or a table in their warehouse. Targets are set at tenant, project or dataset level, each overriding the one above. Where a warehouse is the target, old versions remain replayable only within its time-travel retention.
- **Integrity.** The platform owns its prefix or schema within customer storage. Manifests carry checksums, so out-of-band modification is detected and the affected version flagged.
- **Retention.** Either delegated to the platform, which then deletes expired versions in customer storage, or left to the customer's own lifecycle rules, in which case the platform detects missing files and marks the version expired.
- **Adoption.** Registering in place means taking a table over in place or adopting existing files under a manifest of the platform's own ([D51](0051-adoption-of-existing-data.md)). A managed dataset may then reference files outside the platform-managed prefix, read-only, with size, ETag and modification time recorded in place of checksums, and deleted only if their retention is handed to the platform. Hive-style tables are storage targets.
- **Delivery.** Separately, a sink node may deliver a copy of a dataset into a customer system. A delivered copy is an export, not the dataset: it is neither versioned nor protected by the platform.
- **Uploads.** A file uploaded through the browser, CLI or SDK becomes a managed dataset whose producer is the upload action rather than a workflow. From then on it is versioned, validated, classified, retained and consumed like any other dataset. A dataset is either upload-fed or workflow-fed, never both ([D13](0013-partitioning-intervals-and-dataset-ownership.md)).
- **Upload path.** Bytes go directly to the project's storage target through pre-signed, resumable multipart transfers and never pass through the interface or control planes ([D21](0021-architecture-planes.md)). Checksums are verified on arrival; each upload is a new version, and an identical re-upload is recognized by its digest and recorded as a no-op. The family plugin validates the file at publication, and the schema starts in observed mode (DE 5.8).
- **Originals.** The uploaded file is kept unchanged as the source of truth. Where it helps performance, an optimized copy such as Parquet is produced as a derived artifact, never as a replacement. Amended by [D44](0044-minimum-technology-stack.md): where the Iceberg projection is on, a tabular upload always has a derived Parquet copy, and the copy, not the original, is projected.
- **Intended use.** Uploads suit reference, sample and labeled data and models. Bulk data is connected or registered in place; very large files use the CLI or SDK with the same mechanism. The cloud edition caps the size of browser uploads.
