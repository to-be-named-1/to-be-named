## Failure and scaling

### Leader failure

The leader's hot state — queues and fair-share usage per capacity domain, lease renewals, and the counters of map groups and of each run's outstanding task runs — lives in its memory. A standby that takes leadership increments the epoch, waits one transaction timeout and a margin so that the old leader's transactions have ended, rebuilds that state from Postgres and treats every active attempt as renewed; agents' retries then reach it ([D47]({workspace}/decisions/Platform#47)). The [leader failover](05-key-flows.md#5.6) flow shows the sequence.

### Invariants in the database

Nothing correct depends on leadership being exclusive. Row locks, conditional updates and unique constraints enforce the invariants of each aggregate, and every leader-only transaction checks the epoch, so an overlap of two leaders costs fairness, not correctness ([D47]({workspace}/decisions/Platform#47)).

### Control-plane outage

An outage of the whole control plane stops new dispatch and commits, but not running work ([D21]({workspace}/decisions/Platform#21)). Side-effecting steps pause, since they cannot confirm their leases, and agents buffer their commit requests ([D40]({workspace}/decisions/Platform#40)). After a restart, no lease is declared lost until a grace period of at least one lease duration has passed, so the outage itself fails no work ([D40]({workspace}/decisions/Platform#40), [D43]({workspace}/decisions/Platform#43)).

### Lost events

Every action triggered by an event has a level-triggered sweep behind it, which finds runs whose task runs have all ended, completed map groups, attempts offered but never claimed and expired holds, so a lost or poisoned event delays work rather than stalling it ([D47]({workspace}/decisions/Platform#47)). Outbox rows and work rows are retried with back-off and jitter; a row that exhausts its attempts becomes a dead letter, which raises an alert and can be re-driven. Delivery lag, the age of the oldest undelivered row and dead letters are exported as metrics ([D48]({workspace}/decisions/Platform#48)). Between processes, a wake-up is a NOTIFY hint sent after commit, and polling is the guarantee ([D48]({workspace}/decisions/Platform#48)).

### Routing to roles

Which processes run the `api` role is fixed at deployment, so API traffic reaches them by membership: on Kubernetes, a Service selects the pods whose template carries the role; elsewhere, only `api` processes are registered with the load balancer. The process holding the `leader` role changes at every failover, so agent traffic reaches it by detection. The leader opens the agent port only while it holds leadership. On Kubernetes, it labels its own pod with the `leader` role and an agent Service selects that label; behind other load balancers, a health check on the agent endpoint that only the leader passes routes agents to it. An agent call that reaches another process fails and is retried, so retries remain the fallback in every deployment ([D47]({workspace}/decisions/Platform#47)).

A process reports readiness for the role that receives traffic through it, so a stuck background loop does not take a healthy API out of rotation. Its liveness combines a progress check for each of its roles and fails when any of them stops, so a half-working process is restarted ([D47]({workspace}/decisions/Platform#47)).

### Scaling

Roles scale user traffic (`api`), and planning, reconciliation and event delivery (`worker`), by adding processes. They do not scale the leader, whose state is held in memory; a hosted control plane scales beyond one leader by cells, each with its own database and a set of tenants ([D47]({workspace}/decisions/Platform#47)). The scale targets are those of [D43]({workspace}/decisions/Platform#43).

Three seams keep a cache or message broker possible without changing producers or consumers, each implemented in-process: an event relay, so that producers only ever write the outbox; a change feed for live interface updates; and a rate limiter for per-tenant limits on a hosted control plane ([D47]({workspace}/decisions/Platform#47)).
