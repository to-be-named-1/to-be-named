## Security

Row-level security enforces the tenant, the hard boundary between tenants; project scope, roles and visibility are enforced by the control plane's authorization layer ([D30]({workspace}/decisions/Platform#30), [D45]({workspace}/decisions/Platform#45)).

- **Forced on every table.** Every table has row-level security enabled and forced, since table owners otherwise bypass it, and a table with no policy denies everything ([D45]({workspace}/decisions/Platform#45)).
- **Failing closed.** Each transaction sets its tenant with a transaction-local setting, which policies read and cast to the identifier type, so a transaction that has not set it fails with an error rather than seeing every tenant's rows ([D45]({workspace}/decisions/Platform#45)).
- **The tenant in every key.** The tenant leads every primary key and is part of every unique constraint and foreign key, because Postgres checks them outside row-level security ([D42]({workspace}/decisions/Platform#42), [D45]({workspace}/decisions/Platform#45)).
- **Views and partitions.** Views are created with `security_invoker`, and partitioned tables are read only through their parents, so the caller's policies always apply ([D45]({workspace}/decisions/Platform#45)).
- **The leader epoch.** The epoch belongs to no tenant: its policy lets every tenant-scoped transaction read it, since leader-only transactions check it, and only leadership changes it, through the system role ([D45]({workspace}/decisions/Platform#45), [D47]({workspace}/decisions/Platform#47)).
- **Checked in CI.** CI checks that every table has row-level security enabled and forced with a policy, that every unique constraint and foreign key includes the tenant, and that no query run for one tenant returns data seeded for another ([D45]({workspace}/decisions/Platform#45)).

Platform staff have no standing access to tenant records on a hosted control plane; support access is break-glass: time-limited, audited and visible to the tenant ([D45]({workspace}/decisions/Platform#45)).
