# 47. Control-plane structure

Date: 2026-10-11

## Status

Accepted

Amends [8. Cache keying](0008-cache-keying.md)
Amends [21. Architecture planes](0021-architecture-planes.md)
Amends [27. Ibis for relational node definitions](0027-ibis-for-relational-node-definitions.md)
Amends [31. Execution state model](0031-execution-state-model.md)
Amends [34. Capacity and size](0034-capacity-and-size.md)
Amends [43. Scheduling and capacity](0043-scheduling-and-capacity.md)
Amends [45. Isolation enforcement and role model](0045-isolation-enforcement-and-role-model.md)
Amended by [50. Development mode](0050-development-mode.md)

## Context

Content pending migration; authoritative text: project-design.md v0.10, D47.

## Amendment history

- 2026-10-11: The control-plane binary may be deployed in roles: `api` (ConnectRPC for the web application and the CLI, serving the single-page application, and refusing agent calls as retryable), `worker` (planning, reconciler loops, outbox and work-row handlers, watching the deploy branch and collection marking), `leader` (eligible for leader election; when elected, it runs the agent gateway, the scheduler, the dispatcher and run advancement) and `all`, the default, which runs everything, so that a single-machine installation runs one process. A process may combine roles, and each process reports readiness for its own roles. In-process wake-ups remain an optimization within a process; between processes, wake-ups are NOTIFY hints with polling as the guarantee ([D48](0048-execution-mechanics.md)). Roles scale user traffic, planning, reconciliation and event delivery; they do not scale the leader, whose state is held in memory ([D43](0043-scheduling-and-capacity.md)), and beyond it the route remains cells. In the architecture model the server is one container whose components carry a `roles` property, and the deployment views show instances by role.
