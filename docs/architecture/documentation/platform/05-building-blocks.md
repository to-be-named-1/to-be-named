## Building blocks

![](embed:containers)

The platform's containers are grouped by plane. Logs and metrics go to the observability service, or to the customer's own observability stack where the customer keeps them in its environment ([D40]({workspace}/decisions/Platform#40)). Three further views show each part of the platform with the people and external systems it works with.

### Containers

| Plane | Container | Technology | Responsibility | Decisions |
|---|---|---|---|---|
| Interface | Web application | React, TypeScript, Vite, React Flow 12, ELK | Canvas, runs, datasets, lineage and administration; served by the control-plane binary | [D1]({workspace}/decisions/Platform#1), [D2]({workspace}/decisions/Platform#2), [D4]({workspace}/decisions/Platform#4), [D24]({workspace}/decisions/Platform#24), [D41]({workspace}/decisions/Platform#41), [D44]({workspace}/decisions/Platform#44), [D45]({workspace}/decisions/Platform#45), [D46]({workspace}/decisions/Platform#46) |
| Interface | CLI | Not decided | Command-line client of the API | [D4]({workspace}/decisions/Platform#4), [D44]({workspace}/decisions/Platform#44) |
| Control | [Control-plane server]({workspace}/documentation/Platform/Control-plane%20server#1) | Go, ConnectRPC, cel-go | Compiles, plans, schedules and dispatches work, makes results current and holds the catalog; deployed in roles with a single active leader | [D1]({workspace}/decisions/Platform#1), [D2]({workspace}/decisions/Platform#2), [D3]({workspace}/decisions/Platform#3), [D4]({workspace}/decisions/Platform#4), [D13]({workspace}/decisions/Platform#13), [D14]({workspace}/decisions/Platform#14), [D15]({workspace}/decisions/Platform#15), [D16]({workspace}/decisions/Platform#16), [D17]({workspace}/decisions/Platform#17), [D18]({workspace}/decisions/Platform#18), [D19]({workspace}/decisions/Platform#19), [D20]({workspace}/decisions/Platform#20), [D21]({workspace}/decisions/Platform#21), [D23]({workspace}/decisions/Platform#23), [D24]({workspace}/decisions/Platform#24), [D25]({workspace}/decisions/Platform#25), [D26]({workspace}/decisions/Platform#26), [D28]({workspace}/decisions/Platform#28), [D29]({workspace}/decisions/Platform#29), [D30]({workspace}/decisions/Platform#30), [D31]({workspace}/decisions/Platform#31), [D32]({workspace}/decisions/Platform#32), [D33]({workspace}/decisions/Platform#33), [D34]({workspace}/decisions/Platform#34), [D40]({workspace}/decisions/Platform#40), [D41]({workspace}/decisions/Platform#41), [D43]({workspace}/decisions/Platform#43), [D44]({workspace}/decisions/Platform#44), [D45]({workspace}/decisions/Platform#45), [D46]({workspace}/decisions/Platform#46), [D47]({workspace}/decisions/Platform#47), [D48]({workspace}/decisions/Platform#48), [D49]({workspace}/decisions/Platform#49), [D51]({workspace}/decisions/Platform#51), [D52]({workspace}/decisions/Platform#52), [D55]({workspace}/decisions/Platform#55) |
| Control | [Control-plane database]({workspace}/documentation/Platform/Control-plane%20database#1) | PostgreSQL 17+ | The only stateful dependency, with one schema per bounded context | [D30]({workspace}/decisions/Platform#30), [D42]({workspace}/decisions/Platform#42), [D44]({workspace}/decisions/Platform#44), [D45]({workspace}/decisions/Platform#45), [D47]({workspace}/decisions/Platform#47), [D48]({workspace}/decisions/Platform#48) |
| Data | Execution agent | Go, static binary | Pulls work, launches units, mints credentials, resolves secrets; the single egress | [D21]({workspace}/decisions/Platform#21), [D22]({workspace}/decisions/Platform#22), [D26]({workspace}/decisions/Platform#26), [D28]({workspace}/decisions/Platform#28), [D29]({workspace}/decisions/Platform#29), [D30]({workspace}/decisions/Platform#30), [D40]({workspace}/decisions/Platform#40), [D43]({workspace}/decisions/Platform#43), [D44]({workspace}/decisions/Platform#44), [D48]({workspace}/decisions/Platform#48), [D49]({workspace}/decisions/Platform#49), [D52]({workspace}/decisions/Platform#52) |
| Data | Built-in secret store | Not decided | Secrets on the data-plane side where no customer secret manager exists | [D40]({workspace}/decisions/Platform#40) |
| Data | Unit runtime | Python, Ibis on DuckDB, Polars | Runs one execution unit's engine segments and requests its commit | [D15]({workspace}/decisions/Platform#15), [D17]({workspace}/decisions/Platform#17), [D18]({workspace}/decisions/Platform#18), [D23]({workspace}/decisions/Platform#23), [D25]({workspace}/decisions/Platform#25), [D27]({workspace}/decisions/Platform#27), [D32]({workspace}/decisions/Platform#32), [D34]({workspace}/decisions/Platform#34), [D40]({workspace}/decisions/Platform#40), [D44]({workspace}/decisions/Platform#44), [D46]({workspace}/decisions/Platform#46), [D49]({workspace}/decisions/Platform#49) |
| Data | Session unit | Python | Runs one author's successive interactive sample runs, each unit in a fresh process | [D50]({workspace}/decisions/Platform#50) |
| Data | Command unit | Not decided | Runs a command-line tool's image as a unit | [D32]({workspace}/decisions/Platform#32) |
| Data | Projection unit | Python, PyIceberg | Projects committed versions as Iceberg snapshots for external engines | [D42]({workspace}/decisions/Platform#42), [D44]({workspace}/decisions/Platform#44) |
| Data | Publication unit | Python | Commits current versions to storage targets that have their own commit: Iceberg and Delta tables and Hive-style tables | [D15]({workspace}/decisions/Platform#15), [D55]({workspace}/decisions/Platform#55) |
| Data | Probe unit | Python | Fixes external sources' versions or positions at run start, checks and scans existing data at adoption, and observes external producers | [D49]({workspace}/decisions/Platform#49), [D51]({workspace}/decisions/Platform#51) |
| Data | Sample-building unit | Python, DuckDB | Builds the samples that sample runs read | [D50]({workspace}/decisions/Platform#50) |
| Data | Bundled object storage | Not decided ([S25]({workspace}/documentation#3.1)) | Default storage target of self-hosted installations without object storage of their own | [D4]({workspace}/decisions/Platform#4), [D23]({workspace}/decisions/Platform#23) |
| Observability | Observability service | Not decided | Receives logs, metrics and node events, redacts secrets on ingestion, serves the live log tail and the archive, and raises alerts | [D21]({workspace}/decisions/Platform#21), [D40]({workspace}/decisions/Platform#40) |

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

Self-hosted installations without object storage of their own use the bundled object storage as their default storage target ([S25]({workspace}/documentation#3.1)).
