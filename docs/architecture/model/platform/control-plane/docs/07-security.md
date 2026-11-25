## Security

### People and automation

The API layer authenticates people through local accounts or an identity provider over OpenID Connect; authentication is an extension point, behind which SAML single sign-on and SCIM provisioning sit in the proprietary edition ([D53]({workspace}/decisions/Platform#53)). Service accounts are the principals of CI and automation ([D45]({workspace}/decisions/Platform#45)).

The authorization layer checks every API method against the caller's role bindings before its handler runs: project scope, fixed roles and clearance ([D45]({workspace}/decisions/Platform#45)). A resource the caller cannot read is reported as not found rather than forbidden, and lists are filtered in the query ([D30]({workspace}/decisions/Platform#30), [D45]({workspace}/decisions/Platform#45)). The policy behind the layer is an extension point, through which custom roles and attribute-based policy are added ([D45]({workspace}/decisions/Platform#45), [D53]({workspace}/decisions/Platform#53)).

A run acts with its project's permissions, not those of whoever triggered it; its access is checked when it is planned and recorded in the plan ([D45]({workspace}/decisions/Platform#45)).

### Tenant isolation

Every query runs through one helper that opens a transaction scoped to one tenant, and row-level security in the database enforces the tenant as the hard boundary; project scope, roles and visibility are enforced by the authorization layer ([D30]({workspace}/decisions/Platform#30), [D45]({workspace}/decisions/Platform#45)). Only the components named under system scope reach the connection pool of the system role, which finds work across tenants; every change to a tenant's records happens in a transaction scoped to that tenant ([D45]({workspace}/decisions/Platform#45)). The [database documentation]({workspace}/documentation/Platform/Control-plane%20database#4) describes the database's side.

### Node code

The server reads code nodes without executing them, in a worker process that reads neither storage nor the network, keeps nothing between requests and works within limits on time, memory and input size; node code itself runs only in the data plane ([D21]({workspace}/decisions/Platform#21), [D68]({workspace}/decisions/Platform#68)).

### Agents

Agents are not principals. An agent installation enrolls with a one-time token whose secret never travels, registering an enrollment key bound to its tenant and pool; each replica registers a key of its own with it, held in memory and rotated automatically, and the use of a key that was rotated out marks its enrollment compromised ([D64]({workspace}/decisions/Platform#64)). The replica signs every request, and the server signs every response with a key its root key delegates, with HTTP Message Signatures using Ed25519; bodies are covered through Content-Digest, and a response's signature also covers the request it answers ([D52]({workspace}/decisions/Platform#52)). Replays and delays are handled by idempotency, per-attempt sequence numbers and nonces the leader rotates every heartbeat interval, never by wall-clock time ([D44]({workspace}/decisions/Platform#44), [D64]({workspace}/decisions/Platform#64)). Agent endpoints are rate-limited before signatures are verified ([D52]({workspace}/decisions/Platform#52)). Agent-facing methods check that the agent is authorized for the attempt's tenant ([D43]({workspace}/decisions/Platform#43), [D45]({workspace}/decisions/Platform#45)). TLS carries every connection, for confidentiality.

### Credentials and secrets

The server holds no credentials and no secret values. Leases carry credential scopes and secret references; the agent mints short-lived storage credentials, narrowed to each attempt's scopes, and resolves secrets in the customer environment ([D40]({workspace}/decisions/Platform#40), [D65]({workspace}/decisions/Platform#65)). The server holds each pool's certificate authority, with which it certifies the address at which each replica serves units ([D65]({workspace}/decisions/Platform#65)).

### Audit

Authorization decisions on changes and on data access are audited, and so are commits the platform pushes on an author's behalf and releases of quarantined versions ([D45]({workspace}/decisions/Platform#45)). Admins view the audit log in the platform; export to external sinks is an extension point of the proprietary edition ([D53]({workspace}/decisions/Platform#53)).
