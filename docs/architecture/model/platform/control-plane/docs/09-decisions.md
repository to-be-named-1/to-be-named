## Decisions

| Decision | What it settles for this container |
|---|---|
| [D21]({workspace}/decisions/Platform#21) | The planes: the control plane holds pointers, never bulk data, runs no untrusted code, and alone makes a result current |
| [D29]({workspace}/decisions/Platform#29) | Agents pull work in every deployment, so the server never calls a backend's API |
| [D30]({workspace}/decisions/Platform#30) | Isolation of tenants and projects on every path that reads, writes, caches or leases |
| [D40]({workspace}/decisions/Platform#40) | The protocol with the data plane: leases with credential scopes and secret references, outage and partition rules, durable commits and message classes |
| [D43]({workspace}/decisions/Platform#43) | Queues, fair share, admission per capacity domain, scale targets and timings |
| [D44]({workspace}/decisions/Platform#44) | Go, ConnectRPC and cel-go; the transport of the agent protocol |
| [D45]({workspace}/decisions/Platform#45) | Row-level security on the tenant, the authorization layer, roles, drafts, deployment and governed fields |
| [D47]({workspace}/decisions/Platform#47) | The structure: topology, deployment roles, routing to roles, leadership, bounded contexts, the planner, the run driver and the reconciler |
| [D48]({workspace}/decisions/Platform#48) | Execution mechanics: fencing tokens, write leases held by the task run, the outbox and wake-ups |
| [D49]({workspace}/decisions/Platform#49) | Source probes resolving external versions at run start |
| [D51]({workspace}/decisions/Platform#51) | Adoption of existing tables and files |
| [D52]({workspace}/decisions/Platform#52) | Agent identity proven by message signatures on every request and response |
