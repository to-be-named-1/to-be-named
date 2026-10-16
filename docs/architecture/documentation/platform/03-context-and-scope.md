## Context and scope

![](embed:context)

The platform serves the people below and works with the external systems that follow. The data consumer and the container registry reach it only through other external systems: the consumer through its query engines, the registry through the backends that pull images from it.

### People

| Person | How they use the platform | Role ([D45]({workspace}/decisions/Platform#45)) |
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
| Git host | History and review of git-connected projects; the platform pushes on authors' behalf and deploys from the deploy branch | [D41]({workspace}/decisions/Platform#41), [D45]({workspace}/decisions/Platform#45) |
| Identity provider | Authenticates people | [D5]({workspace}/decisions/Platform#5), [D45]({workspace}/decisions/Platform#45) |
| Object storage | Artifacts, staged outputs and managed datasets, in platform or customer storage | [D4]({workspace}/decisions/Platform#4), [D23]({workspace}/decisions/Platform#23), [D42]({workspace}/decisions/Platform#42), [D51]({workspace}/decisions/Platform#51) |
| Lakehouse catalog | Where customers' tables are registered, including tables that are storage targets or taken over in place | [D15]({workspace}/decisions/Platform#15), [D51]({workspace}/decisions/Platform#51), [D55]({workspace}/decisions/Platform#55) |
| Iceberg catalog | Where projected tables are registered for external engines | [D42]({workspace}/decisions/Platform#42), [D44]({workspace}/decisions/Platform#44) |
| External query engines | Read managed datasets as Iceberg tables | [D44]({workspace}/decisions/Platform#44) |
| Docker engine, Kubernetes cluster, HPC scheduler, cloud batch service | Backends on which the agent runs units | [D12]({workspace}/decisions/Platform#12), [D22]({workspace}/decisions/Platform#22), [D29]({workspace}/decisions/Platform#29) |
| Container registry | Images that units run, referenced by digest | [D22]({workspace}/decisions/Platform#22) |
| Secret manager | Secrets resolved by the agent from references | [D40]({workspace}/decisions/Platform#40) |
| Cloud credential issuer | Short-lived storage credentials minted by the agent per unit | [D22]({workspace}/decisions/Platform#22), [D40]({workspace}/decisions/Platform#40) |
| External data sources | Data that workflows read without the platform owning it | [D4]({workspace}/decisions/Platform#4), [D35]({workspace}/decisions/Platform#35), [D37]({workspace}/decisions/Platform#37), [D49]({workspace}/decisions/Platform#49), [D51]({workspace}/decisions/Platform#51) |
| Side-effect targets | Systems that nodes write to, message or trigger | [D40]({workspace}/decisions/Platform#40), [D50]({workspace}/decisions/Platform#50) |
| Warehouses | Postgres and Snowflake, for pushdown, extraction and publication | [D25]({workspace}/decisions/Platform#25), [D28]({workspace}/decisions/Platform#28) |
| Customer observability stack | The customer's own log and metrics stores, where telemetry is kept in the customer's environment (CORE 4.7) | [D22]({workspace}/decisions/Platform#22), [D40]({workspace}/decisions/Platform#40) |
| Notification channels | Alerts | — |
| CI system | Starts sample and development runs as a service account | [D45]({workspace}/decisions/Platform#45), [D50]({workspace}/decisions/Platform#50) |

### What crosses the boundary

Agents in the customer's environment connect outward to the control plane and pull work; no inbound connectivity into a customer network is ever required ([D22]({workspace}/decisions/Platform#22), [D29]({workspace}/decisions/Platform#29), [D40]({workspace}/decisions/Platform#40)). Only metadata, statistics, events and pre-computed previews cross to the hosted planes; previews and samples obey the classification of their source dataset, and a customer may disable them for sensitive datasets ([D22]({workspace}/decisions/Platform#22)). A customer may keep logs and metrics in its own environment, with live tailing proxied through the agent ([D22]({workspace}/decisions/Platform#22), [D40]({workspace}/decisions/Platform#40)).
