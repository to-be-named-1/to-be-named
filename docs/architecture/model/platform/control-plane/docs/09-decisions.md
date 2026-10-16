## Decisions

| Decision | What it settles for this container |
|---|---|
| [D1]({workspace}/decisions/Platform#1) | Nodes are not the unit of dispatch: the planner fuses them into execution units |
| [D2]({workspace}/decisions/Platform#2) | Structured control flow: the compiler checks it, and loops unroll into an acyclic run trace |
| [D3]({workspace}/decisions/Platform#3) | The platform's own IR and orchestrator: the control plane owns control flow and state and dispatches units to backends; a whole workflow without loops can be exported to Argo or Airflow |
| [D21]({workspace}/decisions/Platform#21) | The planes: the control plane holds pointers, never bulk data, runs no untrusted code, and alone makes a result current |
| [D25]({workspace}/decisions/Platform#25) | Engine selection by data location: pushdown, the extraction cap, repartition steps and the plan's stated reasons |
| [D26]({workspace}/decisions/Platform#26) | Explicit placement with recorded reasons, location records and cache eligibility, kept for placement constraints |
| [D28]({workspace}/decisions/Platform#28) | Connection policy within which pushdown is placed, query and job tagging, and plan pinning |
| [D29]({workspace}/decisions/Platform#29) | Agents pull work in every deployment, so the server never calls a backend's API |
| [D30]({workspace}/decisions/Platform#30) | Isolation of tenants and projects on every path that reads, writes, caches or leases |
| [D31]({workspace}/decisions/Platform#31) | The execution state model: runs, task runs and attempts with phase and outcome, failure classes, the checkpoint slot, holds and approvals |
| [D32]({workspace}/decisions/Platform#32) | Units as one container with engine segments; nodes bound to an engine at planning |
| [D33]({workspace}/decisions/Platform#33) | Fusion separated into deterministic legality and a replaceable policy, with its version recorded on every plan |
| [D34]({workspace}/decisions/Platform#34) | The capacity check: observed sizes, memory classes, per-unit ceilings and warnings before the run |
| [D40]({workspace}/decisions/Platform#40) | The protocol with the data plane: leases with credential scopes and secret references, outage and partition rules, durable commits and message classes |
| [D41]({workspace}/decisions/Platform#41) | The IR's text form and versioning, semantic-model hashing, port types, and CEL expressions evaluated by the control plane |
| [D43]({workspace}/decisions/Platform#43) | Queues, fair share, admission per capacity domain, scale targets and timings |
| [D44]({workspace}/decisions/Platform#44) | Go, ConnectRPC and cel-go; the transport of the agent protocol |
| [D45]({workspace}/decisions/Platform#45) | Row-level security on the tenant, the authorization layer, roles, drafts, deployment and governed fields |
| [D46]({workspace}/decisions/Platform#46) | Carried state, switch, branch joins, bounded loops with an explicit limit outcome, and loops run unrolled or inside one unit |
| [D47]({workspace}/decisions/Platform#47) | The structure: topology, deployment roles, routing to roles, leadership, bounded contexts, the planner, the run driver and the reconciler |
| [D48]({workspace}/decisions/Platform#48) | Execution mechanics: fencing tokens, write leases held by the task run, the outbox and wake-ups |
| [D49]({workspace}/decisions/Platform#49) | Source probes resolving external versions at run start |
| [D51]({workspace}/decisions/Platform#51) | Adoption of existing tables and files |
| [D52]({workspace}/decisions/Platform#52) | Agent identity proven by message signatures on every request and response |
