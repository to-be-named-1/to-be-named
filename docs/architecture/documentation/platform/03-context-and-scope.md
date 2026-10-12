## Context and scope

![](embed:context)

The platform serves the people below and works with the external systems that follow. The data consumer and the container registry reach it only through other external systems: the consumer through its query engines, the registry through the backends that pull images from it.

### People

| Person | How they use the platform | Role ([D45](../../decisions/0045-isolation-enforcement-and-role-model.md)) |
|---|---|---|
| Workflow author | Builds and tries workflows and commits drafts in the web application; reviews and merges changes in the git host | Developer |
| Operator | Triggers, backfills, pauses and monitors runs | Operator |
| Project maintainer | Manages settings, bindings and deployments; merges changes to the deploy branch | Maintainer |
| Dataset owner | Governs datasets and releases quarantined versions | `dataset.manage` |
| Tenant administrator | Administers members, agent pools, connections and quotas | Admin |
| Auditor | Reads the audit trail | Auditor (`Commercial`) |
| Data consumer | Queries managed datasets with external query engines | — |
| Infrastructure operator | Installs and upgrades a self-hosted control plane and the agents | — |
| Vendor operator | Operates the hosted control plane (`Commercial`) | — |

### External systems

| System | Role | Decisions |
|---|---|---|
| Git host | History and review of git-connected projects; the platform pushes on authors' behalf and deploys from the deploy branch | [D41](../../decisions/0041-ir-text-form-round-trip-and-structure.md), [D45](../../decisions/0045-isolation-enforcement-and-role-model.md) |
| Identity provider | Authenticates people | [D5](../../decisions/0005-distribution-and-tenancy.md), [D45](../../decisions/0045-isolation-enforcement-and-role-model.md) |
| Object storage | Artifacts, staged outputs and managed datasets, in platform or customer storage | [D4](../../decisions/0004-datasets-as-first-class-objects.md), [D23](../../decisions/0023-artifact-storage-layout.md), [D42](../../decisions/0042-catalogue-persistence.md) |
| Iceberg catalogue | Where projected tables are registered for external engines | [D42](../../decisions/0042-catalogue-persistence.md), [D44](../../decisions/0044-minimum-technology-stack.md) |
| External query engines | Read managed datasets as Iceberg tables | [D44](../../decisions/0044-minimum-technology-stack.md) |
| Docker engine, Kubernetes cluster, HPC scheduler, cloud batch service | Backends on which the agent runs units | [D12](../../decisions/0012-streaming-readiness.md), [D22](../../decisions/0022-deployment-topologies.md), [D29](../../decisions/0029-first-development-slice.md) |
| Container registry | Images that units run, referenced by digest | [D22](../../decisions/0022-deployment-topologies.md) |
| Secret manager | Secrets resolved by the agent from references | [D40](../../decisions/0040-protocol-between-the-control-and-data-planes.md) |
| Cloud credential issuer | Short-lived storage credentials minted by the agent per unit | [D22](../../decisions/0022-deployment-topologies.md), [D40](../../decisions/0040-protocol-between-the-control-and-data-planes.md) |
| External data sources | Data that workflows read without the platform owning it | [D4](../../decisions/0004-datasets-as-first-class-objects.md), [D35](../../decisions/0035-ephemeral-extraction.md), [D37](../../decisions/0037-incremental-extraction-state.md), [D49](../../decisions/0049-source-probes.md) |
| Side-effect targets | Systems that nodes write to, message or trigger | [D40](../../decisions/0040-protocol-between-the-control-and-data-planes.md), [D50](../../decisions/0050-development-mode.md) |
| Warehouses | Postgres and Snowflake, for pushdown, extraction and publication | [D25](../../decisions/0025-processing-engines-and-runtimes.md), [D28](../../decisions/0028-warehouse-connection-policy-and-plan-pinning.md) |
| Observability sink | Logs and metrics, the vendor's or the customer's own | [D21](../../decisions/0021-architecture-planes.md), [D40](../../decisions/0040-protocol-between-the-control-and-data-planes.md) |
| Notification channels | Alerts | — |
| CI system | Starts sample and development runs as a service account | [D45](../../decisions/0045-isolation-enforcement-and-role-model.md), [D50](../../decisions/0050-development-mode.md) |

### What crosses the boundary

Agents in the customer's environment connect outward to the control plane and pull work; no inbound connectivity into a customer network is ever required ([D22](../../decisions/0022-deployment-topologies.md), [D29](../../decisions/0029-first-development-slice.md), [D40](../../decisions/0040-protocol-between-the-control-and-data-planes.md)). Only metadata, statistics, events and pre-computed previews cross to the hosted planes; previews and samples obey the classification of their source dataset, and a customer may disable them for sensitive datasets ([D22](../../decisions/0022-deployment-topologies.md)). A customer may keep logs and metrics in its own environment, with live tailing proxied through the agent ([D22](../../decisions/0022-deployment-topologies.md), [D40](../../decisions/0040-protocol-between-the-control-and-data-planes.md)).
