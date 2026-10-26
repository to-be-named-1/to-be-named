## Decisions

| Decision | What it settles for this container |
|---|---|
| [D1]({workspace}/decisions/Platform#1) | Nodes are not the unit of dispatch: the planner fuses them into execution units |
| [D2]({workspace}/decisions/Platform#2) | Structured control flow: the compiler checks it, and loops unroll into an acyclic run trace |
| [D3]({workspace}/decisions/Platform#3) | The platform's own IR and orchestrator: the control plane owns control flow and state and dispatches units to backends; a whole workflow without loops can be exported to Argo or Airflow |
| [D4]({workspace}/decisions/Platform#4) | Datasets as domain objects with versions, partitions and owners; managed or external; storage targets; uploads |
| [D5]({workspace}/decisions/Platform#5) | Tenant identifier on every entity; capabilities likely to be commercial (authentication, access policy, audit sinks, AI providers) behind extension interfaces |
| [D7]({workspace}/decisions/Platform#7) | Tiers per run from the weakest node on each path, static ceilings, Reproducible only through verification, decay |
| [D8]({workspace}/decisions/Platform#8) | Hybrid cache keys chained through nodes, lookups only at unit boundaries, expected reuse before the run and the authoritative lookup at task-run creation |
| [D9]({workspace}/decisions/Platform#9) | Cache reuse within a project by default, across a tenant's projects by opt-in under the permission check, never across tenants |
| [D10]({workspace}/decisions/Platform#10) | Column-level lineage derived for SQL and declarative nodes, task-level across custom code, declared mappings labeled |
| [D12]({workspace}/decisions/Platform#12) | The streaming seams: a neutral execution concept, health from lease renewal, execution modes declared by node types, recorded position ranges, caching as a policy |
| [D13]({workspace}/decisions/Platform#13) | Partitioning and intervals validated against each other, single producers, partition dependency functions |
| [D14]({workspace}/decisions/Platform#14) | Inputs resolved once per run under snapshot isolation, pinning and coherent reads, protection of inputs in use |
| [D15]({workspace}/decisions/Platform#15) | Publication staged per attempt and made current by one catalog commit, publication groups, partially published external targets |
| [D16]({workspace}/decisions/Platform#16) | Per-input readiness policies, waiting without compute, degraded outputs cascading with their cause |
| [D17]({workspace}/decisions/Platform#17) | Dataset families behind one plugin interface; models as a dataset type |
| [D18]({workspace}/decisions/Platform#18) | Format types, pinned implementations and bindings, allowed implementations per project |
| [D19]({workspace}/decisions/Platform#19) | Fixed dataset names over immutable identifiers |
| [D20]({workspace}/decisions/Platform#20) | Backfills committed per interval with downstream work coalesced, atomic restatements, lower priority than scheduled work |
| [D21]({workspace}/decisions/Platform#21) | The planes: the control plane holds pointers, never bulk data, runs no untrusted code, and alone makes a result current |
| [D23]({workspace}/decisions/Platform#23) | Identity-addressed artifact paths and manifests in the catalog, collection by marking |
| [D24]({workspace}/decisions/Platform#24) | Requests to make a dataset current, planned over the project's dataset graph |
| [D25]({workspace}/decisions/Platform#25) | Engine selection by data location: pushdown, the extraction cap, repartition steps and the plan's stated reasons |
| [D26]({workspace}/decisions/Platform#26) | Explicit placement with recorded reasons, location records and cache eligibility, kept for placement constraints |
| [D28]({workspace}/decisions/Platform#28) | Connection policy within which pushdown is placed, query and job tagging, and plan pinning |
| [D29]({workspace}/decisions/Platform#29) | Agents pull work in every deployment, so the server never calls a backend's API |
| [D30]({workspace}/decisions/Platform#30) | Isolation of tenants and projects on every path that reads, writes, caches or leases |
| [D31]({workspace}/decisions/Platform#31) | The execution state model: runs, task runs and attempts with phase and outcome, failure classes, the checkpoint slot, holds and approvals |
| [D32]({workspace}/decisions/Platform#32) | Units as one container with engine segments; nodes bound to an engine at planning |
| [D33]({workspace}/decisions/Platform#33) | Fusion separated into deterministic legality and a replaceable policy, with its version recorded on every plan |
| [D34]({workspace}/decisions/Platform#34) | The capacity check: observed sizes, memory classes, per-unit ceilings and warnings before the run |
| [D35]({workspace}/decisions/Platform#35) | Ephemeral or copied source reads chosen by the author, source versions recorded on every read |
| [D36]({workspace}/decisions/Platform#36) | Reproducibility behaviors opt-in through one project setting; ordinary retention governs; guard rails as overridable warnings |
| [D37]({workspace}/decisions/Platform#37) | Cursors derived from position records committed with the data, the frontier, bootstrap, resets and queueing on cursor-based sources |
| [D38]({workspace}/decisions/Platform#38) | As-of queries over commit history, answered only below the commit watermark |
| [D40]({workspace}/decisions/Platform#40) | The protocol with the data plane: leases with credential scopes and secret references, outage and partition rules, durable commits and message classes |
| [D41]({workspace}/decisions/Platform#41) | The IR's text form and versioning, semantic-model hashing, port types, and CEL expressions evaluated by the control plane |
| [D42]({workspace}/decisions/Platform#42) | How the catalog is persisted: partition versions by validity interval, commit ordering and the watermark, the commit transaction, read records, the control-plane boundary, identifiers and external readability |
| [D43]({workspace}/decisions/Platform#43) | Queues, fair share, admission per capacity domain, scale targets and timings |
| [D44]({workspace}/decisions/Platform#44) | Go, ConnectRPC and cel-go; the transport of the agent protocol |
| [D45]({workspace}/decisions/Platform#45) | Row-level security on the tenant, the authorization layer, roles, drafts, deployment and governed fields |
| [D46]({workspace}/decisions/Platform#46) | Carried state, switch, branch joins, bounded loops with an explicit limit outcome, and loops run unrolled or inside one unit |
| [D47]({workspace}/decisions/Platform#47) | The structure: topology, deployment roles, routing to roles, leadership, bounded contexts, the planner, the run driver and the reconciler |
| [D48]({workspace}/decisions/Platform#48) | Execution mechanics: fencing tokens, write leases held by the task run, the outbox and wake-ups |
| [D49]({workspace}/decisions/Platform#49) | Source probes resolving external versions at run start |
| [D50]({workspace}/decisions/Platform#50) | Development runs: sample and full-scale, selection boundaries, sandboxes as lines, reuse across modes, sampling, development bindings and suppressed side effects, reads bounded by clearance, the best-effort class and a development share |
| [D51]({workspace}/decisions/Platform#51) | Adoption of existing tables and files |
| [D52]({workspace}/decisions/Platform#52) | Agent identity proven by message signatures on every request and response |
| [D55]({workspace}/decisions/Platform#55) | Commits to table-format storage targets made after the platform's commit, by publication units, in version order |
| [D56]({workspace}/decisions/Platform#56) | The envelope and IR version of every committed document, identifiers and generated node keys, node identity across renames, the YAML subset and its data model, and the schema the compiler embeds and validates against |
| [D57]({workspace}/decisions/Platform#57) | The node-type contract the compiler and planner read: runtimes, ports, typed parameters and the checks on expressions in them, derived memory behavior, contracts of code nodes derived from their code, derived schemas and compiled plans obtained from the data plane, engine overrides after hard constraints, and how a fused unit's request is combined |
| [D59]({workspace}/decisions/Platform#59) | Column lineage recorded per run and per column, derived, declared or task-level, which the provenance read model serves |
