## Responsibility

The control-plane server holds the platform's decisions and records. It compiles definitions, plans runs, schedules work and dispatches it to agents, advances runs, makes outputs current in the catalog, and serves the API through which people, the CLI and CI reach the platform ([D21]({workspace}/decisions/Platform#21), [D47]({workspace}/decisions/Platform#47)). It is one Go binary deployed in roles, with a single active leader among the processes eligible to lead ([D47]({workspace}/decisions/Platform#47)).

It never handles the data itself:

- It never reads or writes data. Bulk data stays in the data plane, and the server holds manifests and pointers to it ([D21]({workspace}/decisions/Platform#21), [D42]({workspace}/decisions/Platform#42)).
- It never contacts data sources, warehouses or execution backends. Agents connect out to it and pull work, in every deployment ([D29]({workspace}/decisions/Platform#29), [D40]({workspace}/decisions/Platform#40)).
- It never holds credentials or secret values. Leases carry credential scopes and secret references, and the agent mints credentials and resolves secrets in the customer environment ([D40]({workspace}/decisions/Platform#40)).
- It never runs untrusted code ([D21]({workspace}/decisions/Platform#21)).

Only the control plane makes a result current. A unit stages its outputs and requests the commit through its agent; the server checks the attempt's fencing token and write leases and commits in one transaction ([D15]({workspace}/decisions/Platform#15), [D48]({workspace}/decisions/Platform#48)).

Its durable state is held in the control-plane database, its only stateful dependency; the hot state of scheduling and leases is held in the leader's memory and rebuilt from the database at takeover ([D47]({workspace}/decisions/Platform#47)).
