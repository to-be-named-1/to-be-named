## State

### Durable state

All durable state is held in the control-plane database: one schema per bounded context, and a shared schema for the outbox and the leader epoch. The [database documentation]({workspace}/documentation/Platform/Control-plane%20database#3) lists each schema and the components that reach it. Every transaction is scoped to one tenant, except the work across tenants that [D45]({workspace}/decisions/Platform#45) assigns to the system role.

Processes other than the leader hold no state that correctness depends on: they claim their work — work rows and outbox rows — from the database ([D47]({workspace}/decisions/Platform#47), [D48]({workspace}/decisions/Platform#48)).

### Hot state on the leader

The leader holds the state of scheduling and leases in memory, so that renewals and admission make no database writes, and rebuilds it from the database when it takes leadership ([D43]({workspace}/decisions/Platform#43), [D47]({workspace}/decisions/Platform#47), [D48]({workspace}/decisions/Platform#48)).

| State | Rebuilt from |
|---|---|
| Queues and fair-share usage per capacity domain | Ready task runs, and usage persisted or derived from attempts, so that a failover does not reset fair share ([D43]({workspace}/decisions/Platform#43)) |
| Lease renewals | Active attempts, each treated as renewed at takeover; a lease is declared lost only after a grace period of at least one lease duration ([D40]({workspace}/decisions/Platform#40), [D48]({workspace}/decisions/Platform#48)) |
| Map-group counters and each run's count of outstanding task runs | Recounted at takeover; the counters are written in batches while the leader runs ([D47]({workspace}/decisions/Platform#47)) |

Correctness never depends on this state: the database's row locks, conditional updates and unique constraints enforce the invariants ([D47]({workspace}/decisions/Platform#47)).

### Clocks

Durable timestamps and due times come from the database clock. Lease timing uses the leader's monotonic clock, and lease durations are relative to receipt, never absolute timestamps ([D40]({workspace}/decisions/Platform#40), [D47]({workspace}/decisions/Platform#47)).
