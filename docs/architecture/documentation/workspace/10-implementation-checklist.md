## Implementation checklist

An item blocks the start of development only if the first code would build it into something expensive to change later: a persisted schema, the wire protocol that runs inside customer environments, or the IR format that users commit to git. An item whose later correction only costs performance, such as extra cache misses, or is purely additive, waits.

### Decided seams the first schema must include

- Tenant identifier on every entity ([D5]({workspace}/decisions/Platform#5))
- Immutable dataset identifier ([D19]({workspace}/decisions/Platform#19))
- Schema version in the IR ([D3]({workspace}/decisions/Platform#3))
- Separate semantic and operational fields ([D8]({workspace}/decisions/Platform#8))
- Phase separate from outcome ([D12]({workspace}/decisions/Platform#12) Seam 1, [D31]({workspace}/decisions/Platform#31))
- Failure classes on attempts, checkpoint slots on task runs and the reused outcome ([D31]({workspace}/decisions/Platform#31))
- Memory class on node types ([D34]({workspace}/decisions/Platform#34))
- Execution-mode field on node types ([D12]({workspace}/decisions/Platform#12) Seam 3)
- Read positions consumed ([D12]({workspace}/decisions/Platform#12) Seam 4)
- Metrics as time series ([D12]({workspace}/decisions/Platform#12) Seam 10)
- Backend lifecycle interface ([D12]({workspace}/decisions/Platform#12) Seam 9)
- Attempt-scoped staging with fencing tokens on commits ([D15]({workspace}/decisions/Platform#15))
- Backend and region of every attempt and artifact ([D26]({workspace}/decisions/Platform#26) Seam 1)
- Eligibility filter on cache hits ([D26]({workspace}/decisions/Platform#26) Seam 2)
- Placement and its reason recorded by the planner ([D26]({workspace}/decisions/Platform#26) Seam 3)
- Query and job tagging ([D28]({workspace}/decisions/Platform#28))
- Byte and row counts per partition on every manifest, and capacity ceilings per backend ([D34]({workspace}/decisions/Platform#34))
- Commentable IR collections keyed by stable identifier, partition keys stored as columns in managed tabular data, and agent identity checked as possession of the enrolled key ([D44]({workspace}/decisions/Platform#44))
- Row-level security enabled and forced on every table, the tenant in every unique constraint and foreign key, owner, application and system database roles, a permission annotation on every API method, clearance on memberships, and drafts held apart from committed definitions ([D45]({workspace}/decisions/Platform#45))
- An execution-mode field and declared carried state on loop frames, and the loop scope in expressions ([D46]({workspace}/decisions/Platform#46))
- The tenant on every agent message and agent internals keyed by tenant ([D43]({workspace}/decisions/Platform#43))
- A leader epoch row, a unique key per workflow, trigger and logical interval for scheduled runs, and uncompressed sizes among manifest statistics ([D47]({workspace}/decisions/Platform#47))
- Phase, sub-state and outcome columns with their check constraints, the held attempt outcome, timestamps per key transition, write leases held by task runs, and outbox rows per event and handler carrying an ordering key and aggregate version ([D48]({workspace}/decisions/Platform#48))
- Probed positions on external source declarations and read records ([D49]({workspace}/decisions/Platform#49))
- The development fields on runs, run, task-run and attempt tables partitioned by mode as well as time, lines on heads, versions, partition versions, write leases and outbox rows with the line in their unique constraints, a sandbox table, mode and pool on cache-index entries, sample artifacts keyed by their sample specification, and session leases in the agent protocol ([D50]({workspace}/decisions/Platform#50))
- Column lineage recorded per run and per column, with its label: derived, declared or task-level ([D59]({workspace}/decisions/Platform#59))
- Extension interfaces for authentication, policy, audit and AI ([D5]({workspace}/decisions/Platform#5))

### Settled when the work reaches them

| Item | Settled before |
|---|---|
| Ibis spike ([D27]({workspace}/decisions/Platform#27)) | Any built-in relational node or palette design |
| Iceberg interoperability spike ([D44]({workspace}/decisions/Platform#44)) | Implementing the Iceberg projection |
| Minimal long-running execution ([D12]({workspace}/decisions/Platform#12)) | Declaring the execution model settled; an early milestone |
| Authentication and identity provider | Multi-user interface work |
| Image builder and registry | [CORE 1.10](03-capabilities-core.md) |
| Observability stack | The log and metrics pipeline |
| Canvas-side CEL checking ([D44]({workspace}/decisions/Platform#44)) | The expression editor in the visual builder |
| Comment preservation on write-back ([D44]({workspace}/decisions/Platform#44)) | When taken up; additive while IR collections stay keyed by identifier |
| Custom roles and attribute-based policy ([D45]({workspace}/decisions/Platform#45)) | Demand beyond the fixed roles; behind the policy extension ([D5]({workspace}/decisions/Platform#5)) |
| Break-glass support access procedure ([D45]({workspace}/decisions/Platform#45)) | Operating a hosted control plane |
| Mapping git authors to principals ([D45]({workspace}/decisions/Platform#45)) | Deploying git-connected projects with checks on governed fields |
| Engine family in the cache key ([D25]({workspace}/decisions/Platform#25)) | Cache implementation; an error only causes extra misses |
| Split semantics for leakage prevention ([DS 2.8](05-capabilities-ds.md)) | The data-science palette; the IR leaves room for it |
| Broker or cache behind the event-relay, change-feed or rate-limiter seams ([D47]({workspace}/decisions/Platform#47)) | Load tests missing the targets of [D43]({workspace}/decisions/Platform#43), or a hosted control plane at scale |
| Faster probes, for every source kind alike ([D49]({workspace}/decisions/Platform#49), [D58]({workspace}/decisions/Platform#58)) | Measured probe latency |
| Session units and their concurrency ([D50]({workspace}/decisions/Platform#50)) | Measured preview latency on the first slice |
| Two-level warehouse policy, pinned-plan behavior, repartition key (proposals) | Warehouse pushdown and planner work, outside the first slice |

### Set aside

Retention ([S1](07-open-items.md#7.1), [S15](07-open-items.md#7.15)), verification sampling ([S2](07-open-items.md#7.2)), preview sample sizes (S3), archiving ([S5](07-open-items.md#7.5)), placement and residency ([S6](07-open-items.md#7.6), [S23](07-open-items.md#7.23), [D26]({workspace}/decisions/Platform#26)), skew and memory escalation ([S7](07-open-items.md#7.7), [S8](07-open-items.md#7.8)), deprecation and breaking changes ([S16](07-open-items.md#7.16), [S17](07-open-items.md#7.17)), visibility and sharing ([S19](07-open-items.md#7.19), [S20](07-open-items.md#7.20)), lineage export ([S21](07-open-items.md#7.21)), cost attribution ([S22](07-open-items.md#7.22)), the full open/paid line ([D5]({workspace}/decisions/Platform#5), [D53]({workspace}/decisions/Platform#53)), and the deferred follow-ups of [D11]({workspace}/decisions/Platform#11), [D17]({workspace}/decisions/Platform#17), [D18]({workspace}/decisions/Platform#18), [D19]({workspace}/decisions/Platform#19), [D22]({workspace}/decisions/Platform#22), [D24]({workspace}/decisions/Platform#24) and [D25]({workspace}/decisions/Platform#25).
