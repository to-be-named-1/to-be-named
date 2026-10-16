# 15. Atomic publication

Date: 2026-10-11
Applies to: platform.controlPlane, platform.unitRuntime, platform.publicationUnit, lakehouseCatalog

## Status

Accepted

Amended by [48. Execution mechanics](0048-execution-mechanics.md)
Amended by [51. Adoption of existing data](0051-adoption-of-existing-data.md)
Amended by [55. Commits to table-format storage targets](0055-commits-to-table-format-storage-targets.md)

## Decision

Publication stages new data and then makes it current with a single atomic commit. Consumers never observe a partially applied publication, and a retried attempt never publishes twice.

- **Staging.** An execution unit writes new files to a location scoped to its attempt and never overwrites existing files. Quality gates evaluate the staged data; a failed gate prevents the commit and the staged data becomes a quarantined version, which an override may later release ([D31](0031-execution-state-model.md)).
- **Commit point.** For managed datasets the platform's metadata catalog is the commit point: one transaction records the new snapshot manifest, and readers resolve files through the catalog rather than by listing storage paths. Where a managed dataset is stored as a table with its own commit, such as an Iceberg or Delta table or a Hive-style table, that commit follows the platform's, made in the data plane by a publication unit ([D55](0055-commits-to-table-format-storage-targets.md)). This applies uniformly to tabular and non-tabular data. Iceberg metadata projected for external engines is derived from the commit afterwards and never acts as a commit point ([D42](0042-catalog-persistence.md)).
- **External targets.** Publication to an external warehouse uses the target's own transaction, or a staging table followed by a swap. Where the target cannot commit several partitions atomically, partitions are committed individually and the version is reported as **partially published** rather than concealed.
- **Hive-style and taken-over tables.** A Hive-style table commits each partition by repointing its location in the metastore, so a version spanning several partitions is partially published. Platform commits to a table taken over in place carry the dataset and version, and snapshots without them are flagged ([D51](0051-adoption-of-existing-data.md)).
- **Fencing.** Every commit carries the identity of the attempt that produced it. A late commit from an attempt that was presumed lost and has since been retried is rejected. Orphaned staging files are garbage-collected.
- **Open partitions.** Each append to an open partition is its own atomic commit, and marking the partition complete is a further commit (CORE 3.10).
- **Groups.** By default each dataset commits independently. For managed datasets, an author may declare a **publication group** — for example orders and their order lines — whose members commit together or not at all.
- **Fencing token.** Settled by [D48](0048-execution-mechanics.md): the token is the task run and its attempt number. A commit locks the task-run row, requires the attempt to be current and not ended, and requires write leases covering every partition it writes.
