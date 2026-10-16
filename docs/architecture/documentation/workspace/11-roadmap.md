## Roadmap

Phasing is recorded here only; the rest of the documentation describes the target architecture.

### First development slice

Development begins with the slice set by [D29]({workspace}/decisions/Platform#29):

- The tabular dataset family ([D17]({workspace}/decisions/Platform#17)).
- The single-machine container deployment and Kubernetes.
- In-process execution with Ibis on DuckDB, with Polars by justified exception and for code nodes ([D25]({workspace}/decisions/Platform#25), [D27]({workspace}/decisions/Platform#27)).
- The canvas and round-tripping to text in git ([CORE 1.1](03-capabilities-core.md), [CORE 1.6](03-capabilities-core.md)).
- The pull-based agent in every deployment ([D22]({workspace}/decisions/Platform#22), [D29]({workspace}/decisions/Platform#29)).
- Tenant and project isolation on every access path ([D30]({workspace}/decisions/Platform#30)).
- Iceberg metadata projected for managed datasets on object storage ([D42]({workspace}/decisions/Platform#42), [D44]({workspace}/decisions/Platform#44)).

![](embed:containers-first-slice)

### After the first slice

From [D29]({workspace}/decisions/Platform#29): the other five dataset families, HPC agents and cloud batch, warehouse pushdown with connection policy, and the remaining deployment topologies. The license is chosen before the repository is made public ([D5]({workspace}/decisions/Platform#5)).

The model tags as Later the elements the first slice does not build or use: the CLI, the session unit, the command unit and the publication unit; the HPC scheduler, the cloud batch service, warehouses, the lakehouse catalog, notification channels and the CI system.

### Phasing set by decisions

- Comments are not preserved on canvas write-back in the first slice ([D44]({workspace}/decisions/Platform#44), [CORE 1.6](03-capabilities-core.md)).
- The first slice targets 10,000 task runs per run ([D43]({workspace}/decisions/Platform#43), [CORE 2.3](03-capabilities-core.md)).
- The backend and region of every attempt, and the location of every artifact, are recorded from the first release ([D26]({workspace}/decisions/Platform#26), [CORE 2.21](03-capabilities-core.md)).
- Six dataset families are supported in the first release; the first development slice supports the tabular family only ([D17]({workspace}/decisions/Platform#17), [D29]({workspace}/decisions/Platform#29), [CORE 6.15](03-capabilities-core.md)).
- Scope is enforced on every access path from the first slice ([D30]({workspace}/decisions/Platform#30), [CORE 7.1](03-capabilities-core.md)).
- The first release targets Postgres and Snowflake for pushdown, after the first development slice ([D25]({workspace}/decisions/Platform#25), [D29]({workspace}/decisions/Platform#29), [DE 2.1](04-capabilities-de.md)).
- Iceberg metadata is projected from the first slice ([D42]({workspace}/decisions/Platform#42), [DE 3.1](04-capabilities-de.md)).
- Family extension points are internal in the first release ([D17]({workspace}/decisions/Platform#17), [S12](07-open-items.md#7.12)).

### Beyond

Phasing beyond the first slice, from v1 to v2 and whether and when a hosted control plane is operated, is an item of the [design agenda](09-design-agenda.md).

Once code exists, a check is added that the control plane's component groups match its Go package trees.
