## Building blocks

![](embed:containers)

The platform's containers are grouped by plane. The observability plane has no container of its own: logs and metrics go to an external sink ([D21](../../decisions/0021-architecture-planes.md), [D40](../../decisions/0040-protocol-between-the-control-and-data-planes.md)). Three further views show each part of the platform with the people and external systems it works with.

### Containers

| Plane | Container | Technology | Responsibility | Decisions |
|---|---|---|---|---|
| Interface | Web application | React, TypeScript, Vite, React Flow 12, ELK | Canvas, runs, datasets, lineage and administration; served by the control-plane binary | [D41](../../decisions/0041-ir-text-form-round-trip-and-structure.md), [D44](../../decisions/0044-minimum-technology-stack.md), [D45](../../decisions/0045-isolation-enforcement-and-role-model.md) |
| Interface | CLI | Not decided | Command-line client of the API | [D4](../../decisions/0004-datasets-as-first-class-objects.md), [D21](../../decisions/0021-architecture-planes.md), [D44](../../decisions/0044-minimum-technology-stack.md) |
| Control | Control-plane server | Go, ConnectRPC, cel-go | Compiles, plans, schedules and dispatches work, makes results current and holds the catalogue; deployed in roles with a single active leader | [D21](../../decisions/0021-architecture-planes.md), [D44](../../decisions/0044-minimum-technology-stack.md), [D47](../../decisions/0047-control-plane-structure.md), [D48](../../decisions/0048-execution-mechanics.md) |
| Control | Control-plane database | PostgreSQL 17+ | The only stateful dependency, with one schema per bounded context | [D42](../../decisions/0042-catalogue-persistence.md), [D45](../../decisions/0045-isolation-enforcement-and-role-model.md), [D47](../../decisions/0047-control-plane-structure.md) |
| Data | Execution agent | Go, static binary | Pulls work, launches units, mints credentials, resolves secrets; the single egress | [D29](../../decisions/0029-first-development-slice.md), [D40](../../decisions/0040-protocol-between-the-control-and-data-planes.md), [D44](../../decisions/0044-minimum-technology-stack.md), [D48](../../decisions/0048-execution-mechanics.md) |
| Data | Built-in secret store | Not decided | Secrets on the data-plane side where no customer secret manager exists | [D40](../../decisions/0040-protocol-between-the-control-and-data-planes.md) |
| Data | Unit runtime | Python, Ibis on DuckDB, Polars | Runs one execution unit's engine segments and requests its commit | [D25](../../decisions/0025-processing-engines-and-runtimes.md), [D27](../../decisions/0027-ibis-for-relational-node-definitions.md), [D32](../../decisions/0032-execution-unit-structure.md) |
| Data | Session unit | Python | Runs one author's successive interactive sample runs, each unit in a fresh process | [D50](../../decisions/0050-development-mode.md) |
| Data | Command unit | Not decided | Runs a command-line tool's image as a unit | [D32](../../decisions/0032-execution-unit-structure.md) |
| Data | Projection unit | Python, PyIceberg | Projects committed versions as Iceberg snapshots for external engines | [D42](../../decisions/0042-catalogue-persistence.md), [D44](../../decisions/0044-minimum-technology-stack.md) |
| Data | Probe unit | Python | Fixes external sources' versions or positions at run start | [D49](../../decisions/0049-source-probes.md) |
| Data | Sample-building unit | Python, DuckDB | Builds the samples that sample runs read | [D50](../../decisions/0050-development-mode.md) |
| Data | Bundled object storage | Not decided ([S25](../workspace/07-open-items.md)) | Default storage target of self-hosted installations without object storage of their own | [D4](../../decisions/0004-datasets-as-first-class-objects.md) |

### Interface and control planes

![](embed:containers-interface-and-control)

### Execution

![](embed:containers-execution)

### Data access

![](embed:containers-data-access)

### Storage by plane

| Storage | Plane | Holds |
|---|---|---|
| Postgres | Control | Definitions and drafts, runs, datasets, versions, cache index, provenance |
| Object storage (artifact store) | Data | Platform-owned bytes; the control plane holds only pointers |
| Warehouses, lakehouses, user buckets | Data (external) | Referenced data the platform does not own |
| Log archive, time-series store | Observability | Logs, metrics and events |
| Git repositories | Interface | Workflow definitions as text |

Self-hosted installations without object storage of their own use the bundled object storage as their default storage target ([S25](../workspace/07-open-items.md)).
