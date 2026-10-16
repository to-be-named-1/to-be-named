# 28. Warehouse connection policy and plan pinning

Date: 2026-10-11
Applies to: platform.controlPlane, platform.agent, warehouses, workflowAuthor

## Status

Accepted

Amended by [45. Isolation enforcement and role model](0045-isolation-enforcement-and-role-model.md)

## Context

**Pushdown is automatic, within an owner's policy** (D28). Making pushdown opt-in would make "extract everything" the default, which is slower, costlier and worse for governance. But pushdown spends the customer's warehouse resources, so the warehouse owner, not the workflow author, sets the connection policy.

The reasoning on a pure planner, run once per run, in [D47](0047-control-plane-structure.md), also cites this decision.

## Decision

The planner chooses placement automatically, within a policy set on each warehouse connection by the warehouse's owner. Workflow authors may pin the plan of a production workflow so that a change of placement is reported rather than applied.

- **Roles.** The **warehouse owner** sets the connection policy. The **workflow author** sets explicit overrides ([D25](0025-processing-engines-and-runtimes.md)) and may pin a plan. The **planner** places every unit automatically within both. Amended by [D45](0045-isolation-enforcement-and-role-model.md): the warehouse owner is the owner of the connection, a tenant resource granted to projects, and a project's environment bindings may name only connections granted to it.
- **Policy.** Each warehouse connection states whether the platform may compute in that warehouse, which of the warehouse's compute clusters it uses and at what size, and an optional credit budget, whose enforcement is defined together with cost attribution ([S22]({workspace}/documentation#3)).
- **Read-only.** A connection without compute rights makes pushdown unavailable for that warehouse. The planner then extracts within the configured cap or asks the author ([D25](0025-processing-engines-and-runtimes.md)).
- **Defaults.** A new connection allows compute once its owner names a compute cluster, which Snowflake requires for any query. No budget is set by default.
- **No staging.** The policy has no setting for staging data into the warehouse, because the planner writes to a warehouse only to publish a dataset whose storage target is that warehouse ([D25](0025-processing-engines-and-runtimes.md)).
- **Tagging.** Every query the platform runs in a warehouse carries a tag identifying the platform, workflow and run, so that it appears as such in the customer's own query history. Warehouse usage is reported per workflow (CORE 4.5, [S22]({workspace}/documentation#3)). The same applies to every customer backend: jobs on Kubernetes, cloud batch and HPC carry equivalent labels, so that all compute the platform causes on customer infrastructure is attributable ([D22](0022-deployment-topologies.md)).
- **Selection.** Connection policy enters the selection precedence of [D25](0025-processing-engines-and-runtimes.md) at the dialect-capability step: a connection without compute rights is treated as an unavailable dialect. It does not reopen the hard-constraint step deferred by [D26](0026-placement-constraints.md).
- **Pinning.** An author may pin the plan of a workflow. Each run compares its placement with the pinned plan and keeps the pinned placement where it remains possible; a difference is reported to the author. If the pinned placement can no longer be honored, for example because a connection has become read-only, the run stops before execution with an explanation until the author accepts a new plan.
