# 55. Commits to table-format storage targets

Date: 2026-10-16
Applies to: platform.controlPlane, platform.publicationUnit, lakehouseCatalog

## Status

Accepted

Amends [15. Atomic publication](0015-atomic-publication.md)
Amends [23. Artifact storage layout](0023-artifact-storage-layout.md)

## Context

A managed dataset may be stored as a table in the customer's lakehouse, either created by the platform as its storage target ([D4](0004-datasets-as-first-class-objects.md)) or taken over in place ([D51](0051-adoption-of-existing-data.md)). Readers of such a table see only what the table's own commit has added: an Iceberg snapshot registered in its catalog, an entry in a Delta table's log, or a partition location in a Hive metastore. As first recorded, [D15](0015-atomic-publication.md) used that commit "underneath" without saying who makes it or when, relative to the platform's commit point, the Postgres transaction of [D42](0042-catalog-persistence.md). The control plane cannot make it, since it never reaches catalogs or storage ([D21](0021-architecture-planes.md), [D40](0040-protocol-between-the-control-and-data-planes.md)); and a table commit made before the platform's could publish the data of an attempt that is then fenced ([D48](0048-execution-mechanics.md)).

## Decision

The platform's commit remains the only commit point. A table's own commit follows it, made in the data plane by a publication unit.

- **Order.** When a version of a dataset whose storage target has its own commit becomes current, the commit transaction writes an outbox row for its publication, ordered by dataset version ([D48](0048-execution-mechanics.md)). Only committed, unfenced versions reach the table, and they reach it in order.
- **Publication unit.** The dispatcher offers the publication as work to an agent of the pool that holds the table's credentials, as it offers probes and projections; the publication unit commits the version to the table through its catalog or metastore. For Iceberg and Delta tables it adds the files the attempt staged, without rewriting them; for a Hive-style table it repoints each partition, so a version spanning several partitions is partially published ([D51](0051-adoption-of-existing-data.md)).
- **Staging.** An attempt whose output goes to such a table stages its files inside the table's location, so the table's commit adds them without copying.
- **Idempotency.** Every commit to a table carries the dataset and version, as snapshot properties in Iceberg and as an application transaction and commit metadata in Delta ([D51](0051-adoption-of-existing-data.md)). A publication that finds its version already committed does nothing, so a retried or repeated job never commits twice.
- **Visibility.** Readers through the platform see a version when the platform commits it; readers of the table see it once the table's commit has been made. The version records when its table commit succeeded. A table commit that keeps failing becomes a dead letter and raises an alert ([D48](0048-execution-mechanics.md)), and the version is shown as not yet published to its target.
- **Warehouses.** Publication to a warehouse target, by its own transaction or a staging table followed by a swap ([D15](0015-atomic-publication.md)), is settled with the warehouse adapter (design agenda).
- **Amends.** [D15](0015-atomic-publication.md): where a managed dataset is stored as a table with its own commit, that commit follows the platform's. [D23](0023-artifact-storage-layout.md): where the storage target is an Iceberg or Delta table, the manifest lists the files staged for it.

## Rejected alternatives

- Committing the table from the producing unit before the platform's commit, under which a fenced attempt could already have published its data.
- Committing the table from the producing unit once the platform has answered committed, with a job as the fallback when the unit stops first, which makes two paths for one effect.
- A two-phase commit across Postgres and the table's catalog, which needs a coordinator and its recovery for a delay that the outbox already bounds.
- Making the projection unit commit to storage targets as well: a projection is a derived read model that never acts as a commit point, while a commit to a storage target publishes the dataset itself.

## Follow-ups

- Publication to warehouse targets, with the warehouse adapter (design agenda).
