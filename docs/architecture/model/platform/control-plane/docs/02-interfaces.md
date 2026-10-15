## Interfaces

### Provided

| Interface | Used by | Protocol | Served by role |
|---|---|---|---|
| Platform API | Web application, CLI, CI systems | ConnectRPC over HTTPS | `api` |
| Single-page application | Web browsers | HTTPS | `api` |
| Agent protocol | Execution agents | ConnectRPC over HTTPS, signed with HTTP Message Signatures | `leader` |

The platform API is the only way into the platform for people and automation. Every method declares the permission it requires and how its resource is found, as an option on its protobuf definition, and a method without that declaration is refused ([D44]({workspace}/decisions/Platform#44), [D45]({workspace}/decisions/Platform#45)).

The agent protocol is pull-based: agents connect out to the server, make unary calls for state-bearing messages — claims, renewals, state transitions, checkpoint commits, commit requests and end-of-attempt reports — and hold one long-poll per agent replica for offered work and control signals ([D40]({workspace}/decisions/Platform#40), [D44]({workspace}/decisions/Platform#44)). State-bearing messages are guaranteed, idempotent and sequence-numbered per attempt; telemetry does not pass through the control plane ([D21]({workspace}/decisions/Platform#21), [D40]({workspace}/decisions/Platform#40)). Two of the protocol's contracts are versioned separately: the unit specification an offer carries, which is the compiled and resolved plan for one unit rather than the IR, and the protocol itself, negotiated at connection, with a window of agent versions supported, since customers upgrade agents on their own schedule ([D40]({workspace}/decisions/Platform#40)). Every request and response is signed ([D52]({workspace}/decisions/Platform#52)), and agent traffic reaches the leader as described under [failure and scaling](06-failure-and-scaling.md).

### Required

| Interface | Provided by | Protocol | Used for |
|---|---|---|---|
| Authentication | Identity provider | OpenID Connect | Signing people in, where local accounts are not used ([D45]({workspace}/decisions/Platform#45), [D53]({workspace}/decisions/Platform#53)) |
| Git | Git host | HTTPS | Pushing authors' commits and watching the deploy branch ([D45]({workspace}/decisions/Platform#45)) |
| Database | Control-plane database | SQL over pgx | All durable state, through the connections the [database documentation]({workspace}/documentation/Platform/Control-plane%20database#2) describes |
