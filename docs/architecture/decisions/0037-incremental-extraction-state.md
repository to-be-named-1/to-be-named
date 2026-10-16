# 37. Incremental extraction state

Date: 2026-10-11
Applies to: platform.controlPlane, platform.unitRuntime, dataSources

## Status

Accepted

Amended by [49. Source probes](0049-source-probes.md)
Amended by [51. Adoption of existing data](0051-adoption-of-existing-data.md)

## Context

**Cursors derived, not stored** (D37). A separate per-task state store was rejected: it is a second source of truth whose update is not atomic with the data, so a failure between the two loses or duplicates rows. Deriving the cursor from the position record committed with the data makes it advance if and only if the data commits.

## Decision

Incremental extraction keeps no separate per-task state store. The cursor between runs is the end position recorded by the last successfully committed extraction run, derived from catalog metadata the platform already writes.

- **Change detection.** A strategy declared by each connector, with a declared position type: full snapshot (no position; hard deletes found by comparing snapshots by key), watermark polling (a timestamp range; hard deletes missed), append-only key range, log-based change data capture (a log offset; deletes captured), API sync token (an opaque token; deletes usually captured) or file listing (a set of files; deletions found by comparing listings). The platform shows whether a strategy captures hard deletes and offers periodic full-snapshot reconciliation where it does not (DE 1.3).
- **Cursor.** The end position recorded by the last successfully committed extraction run ([D12](0012-streaming-readiness.md) Seam 4, CORE 5.9), written in the same catalog transaction as the commit ([D15](0015-atomic-publication.md)), so the cursor advances if and only if the data commits. Failed and fenced attempts commit nothing, so retries start from the same position. The record is catalog metadata: it survives data retention and does not depend on whether the extracted bytes are kept ([D35](0035-ephemeral-extraction.md)).
- **Frontier.** A per-dataset projection of the furthest committed position, maintained in the same transaction for fast lookup and rebuildable from the position records.
- **Overlap.** Extraction runs on a cursor-based source queue rather than run concurrently (CORE 3.7); single production ([D13](0013-partitioning-intervals-and-dataset-ownership.md)) already guarantees one writer. The queueing is implemented by the write leases of [D43](0043-scheduling-and-capacity.md).
- **Bootstrap.** A first run with no committed position performs a full load and records the position at the snapshot point, such as the log offset at snapshot start (DE 1.4). Where a dataset was adopted, its owner may instead set the starting position at adoption, recorded as the baseline's position, and the first run continues from it ([D51](0051-adoption-of-existing-data.md)).
- **Resets.** Re-synchronizing from scratch or from a given position is a parameter of one run, recorded in its provenance. Re-extracting a past interval produces a new version of that partition and does not rewind the frontier.
- **Clock.** Upper bounds for watermark polling come from the source's clock, not the platform's.
- **Within a run.** Resuming a partially completed extraction uses the checkpoint slot ([D31](0031-execution-state-model.md)), not the cursor.
- **Deletes.** Snapshot-comparison strategies retain a compact key set per run, so detection survives short retention and ephemeral reads.
- **Incremental transforms.** A node that maintains its output incrementally reads the previous version of its own output as an input, through a "latest" partition dependency ([D13](0013-partitioning-intervals-and-dataset-ownership.md)), resolved and recorded under [D14](0014-input-version-resolution.md); it needs no state store either.
- **End position.** Amended by [D49](0049-source-probes.md): the end position of an incremental range is fixed at run start by a source probe, from the source's clock, so the whole range is recorded before anything is read and a retry reads the same range.
