## Interfaces

The control-plane server reaches the database over SQL through pgx, with queries written in SQL and compiled to typed Go by sqlc ([D45]({workspace}/decisions/Platform#45)). It uses three kinds of connection.

| Connection | Database role | Used by | Scope |
|---|---|---|---|
| Application pool | Application role, subject to row-level security | Every component | Each transaction is scoped to one tenant, set by one helper |
| System pool | System role, with `BYPASSRLS` | Only the components named under system scope: outbox and work-row delivery, the scheduler's queues and fair-share state, reconciler wake-ups, collection marking, and leadership for the epoch | Finding work across tenants; never changing a tenant's records |
| Leadership session | — | Leadership, on every process eligible to lead | A session-level advisory lock on a dedicated connection made directly to Postgres, not through a transaction-pooling proxy, released when the session ends |

An owner role runs migrations only ([D45]({workspace}/decisions/Platform#45)). The leadership session is described in [D47]({workspace}/decisions/Platform#47), and the system scope in [D45]({workspace}/decisions/Platform#45).
