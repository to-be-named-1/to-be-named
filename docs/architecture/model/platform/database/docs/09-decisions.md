## Decisions

| Decision | What it settles for this container |
|---|---|
| [D5]({workspace}/decisions/Platform#5) | A tenant identifier on every entity |
| [D12]({workspace}/decisions/Platform#12) | Status vocabularies and schemas not limited to terminal states; dataset versions as append-only sequences with positions |
| [D30]({workspace}/decisions/Platform#30) | Isolation enforced on every path, including persistence |
| [D42]({workspace}/decisions/Platform#42) | How the catalog is stored: partition versions by validity interval, the commit transaction, read records and identifiers |
| [D44]({workspace}/decisions/Platform#44) | PostgreSQL 17 or later |
| [D45]({workspace}/decisions/Platform#45) | Row-level security on the tenant, database roles, failing closed, system scope and data access through sqlc and pgx |
| [D47]({workspace}/decisions/Platform#47) | One schema per bounded context, a shared schema, invariants enforced by the database, and the leader's lock and epoch |
| [D48]({workspace}/decisions/Platform#48) | The outbox: one row per subscribed handler, delivery, retries and dead letters |
| [D50]({workspace}/decisions/Platform#50) | Heads, versions and partition versions keyed by line; development run records in separate time partitions |
