## Responsibility

The control-plane database is the control plane's only stateful dependency: definitions, drafts, runs, the catalog, the cache index, provenance, the outbox and the leader epoch are all held in it, and no cache or message broker sits beside it ([D47]({workspace}/decisions/Platform#47)). Bulk data is never held in it; the catalog keeps manifests, versions and pointers to files in the customer's storage ([D21]({workspace}/decisions/Platform#21), [D42]({workspace}/decisions/Platform#42)).

It is PostgreSQL 17 or later, the first release with `transaction_timeout`, on which the commit path and leader takeover rely ([D42]({workspace}/decisions/Platform#42), [D44]({workspace}/decisions/Platform#44), [D47]({workspace}/decisions/Platform#47)). It is organized as one schema per bounded context of the control plane, and a shared schema for tables that belong to no context. A context's components reach only its own schema; other contexts go through its Go interface ([D47]({workspace}/decisions/Platform#47)).

Only the control-plane server connects to it. Agents, units and the web application reach the control plane through its interfaces, never the database ([D40]({workspace}/decisions/Platform#40)).
