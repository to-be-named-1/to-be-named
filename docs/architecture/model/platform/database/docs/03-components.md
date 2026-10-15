## Schemas

![](embed:components-database)

Each bounded context of the control plane owns one schema, grouped on the diagram like the control-plane components that own it; planning owns no tables. The shared schema holds the tables that belong to no context. No component reaches another context's schema, which the forbidden-edge check enforces on the model ([D47]({workspace}/decisions/Platform#47)).

| Schema | Holds | Owning context | Components that reach it |
|---|---|---|---|
| Identity and tenancy schema | Tenants, principals, memberships, clearance, service accounts, projects, resources and grants, and the audit trail. | Identity and tenancy | Identity and membership, authorization layer, audit |
| Authoring schema | Definitions, drafts, platform-held versions, compiled workflows, deployments and environment bindings. | Authoring | Definitions and drafts, compiler, git synchronization, deployment |
| Plugin registry schema | Format types, implementations, node types, allowed implementations and images. | Plugin registry | Plugin registry |
| Catalog schema | Datasets, versions, partition versions, manifests, positions, frontiers, read records, the cache index, projection state and collection marks. | Catalog | Dataset catalog, cache index, projection scheduling, collection marking, probe scheduling, adoption |
| Orchestration schema | Triggers, materialization requests, backfills, runs and their plans, task runs, attempts, map groups and work rows. | Orchestration | Run driver, reconciler |
| Dispatch schema | Agent pools, capacity domains, agents and their keys, queues and write leases. | Dispatch | Scheduler, dispatcher |
| Provenance schema | Lineage, reproducibility tiers, verification claims and comparator verdicts. | Provenance | Provenance read model |
| Shared schema | Tables owned by no context: the outbox and the leader epoch. | None | Outbox and work-row delivery and leadership; the dataset catalog and the run driver write outbox rows in their own transactions |

Large append-heavy tables, such as task runs, attempts and read records, are designed to be partitionable by time, and the outbox is partitioned by time and emptied by dropping partitions ([D42]({workspace}/decisions/Platform#42), [D48]({workspace}/decisions/Platform#48)).
