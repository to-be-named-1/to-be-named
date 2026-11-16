## Interfaces

### Provided

| Interface | Used by | Protocol | Served by role |
|---|---|---|---|
| Platform API | Web application, CLI, CI systems | ConnectRPC over HTTPS | `api` |
| Single-page application | Web browsers | HTTPS | `api` |
| Agent protocol | Execution agents | ConnectRPC over HTTPS, signed with HTTP Message Signatures | `leader` |

The platform API is the only way into the platform for people and automation. Every method declares the permission it requires and how its resource is found, as an option on its protobuf definition, and a method without that declaration is refused ([D44]({workspace}/decisions/Platform#44), [D45]({workspace}/decisions/Platform#45)).

The agent protocol is pull-based: agent replicas connect out to the server, register a session, make unary calls for state-bearing messages — claims, the transition to running, checkpoint commits, commit requests and end-of-attempt reports — send one heartbeat per replica that renews all its leases, and hold one long-poll per replica for offers and control signals ([D40]({workspace}/decisions/Platform#40), [D44]({workspace}/decisions/Platform#44), [D64]({workspace}/decisions/Platform#64)). State-bearing messages are guaranteed, idempotent and sequence-numbered per attempt, and only the attempt's owner replica sends them; heartbeats are protected by nonces the leader rotates; telemetry does not pass through the control plane, and logs are read from customer storage or, where browsers cannot reach it, relayed for the web application ([D21]({workspace}/decisions/Platform#21), [D40]({workspace}/decisions/Platform#40), [D64]({workspace}/decisions/Platform#64), [D65]({workspace}/decisions/Platform#65)). Two of the protocol's contracts are versioned separately: the unit specification, whose launch part a claim carries and whose execution part passes to the unit unread, and the protocol itself, negotiated when a replica registers, with the current and previous stable major supported, since customers upgrade agents on their own schedule ([D40]({workspace}/decisions/Platform#40), [D64]({workspace}/decisions/Platform#64), [D65]({workspace}/decisions/Platform#65)). Its methods form two services, split by the key that signs them: enrollment and replica registration, and everything else ([D64]({workspace}/decisions/Platform#64)). Every request and response is signed ([D52]({workspace}/decisions/Platform#52)), and agent traffic reaches the leader as described under [failure and scaling](06-failure-and-scaling.md).

### Required

| Interface | Provided by | Protocol | Used for |
|---|---|---|---|
| Authentication | Identity provider | OpenID Connect | Signing people in, where local accounts are not used ([D45]({workspace}/decisions/Platform#45), [D53]({workspace}/decisions/Platform#53)) |
| Git | Git host | HTTPS | Pushing authors' commits and watching the deploy branch ([D45]({workspace}/decisions/Platform#45)) |
| Database | Control-plane database | SQL over pgx | All durable state, through the connections the [database documentation]({workspace}/documentation/Platform/Control-plane%20database#2) describes |
