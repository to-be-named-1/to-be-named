# 21. Architecture planes

Date: 2026-10-11
Applies to: platform, platform.controlPlane, platform.agent, platform.observability

## Status

Accepted

Amended by [40. Protocol between the control and data planes](0040-protocol-between-the-control-and-data-planes.md)
Amended by [47. Control-plane structure](0047-control-plane-structure.md)

## Context

The reasoning on bring-your-own-compute, in [D22](0022-deployment-topologies.md), and on a restricted expression language, in [D41](0041-ir-text-form-round-trip-and-structure.md), rests on this decision.

## Decision

The platform is divided into four planes — interface, control, data and observability — each with a single responsibility and trust level. Storage systems are assigned to planes. The division is illustrated in the [solution strategy](../documentation/platform/04-solution-strategy.md).

- **Invariants.** Bulk data never passes through the interface or control planes. Untrusted code runs only in the data plane. Any data-plane component may be terminated at any moment without loss of correctness. Correctness never depends on observability.
- **Protocol.** The control plane leases work to the data plane with scoped credentials and a fencing token; the data plane returns heartbeats, events and commit requests; only the control plane makes a result current. Amended by [D40](0040-protocol-between-the-control-and-data-planes.md): leases carry credential scopes and secret references, and the agent mints credentials and resolves secrets in the customer environment.
- **Failures.** A control-plane outage stops new dispatch and commits but not running work; a lost data-plane node is recovered by lease expiry and retry; an observability outage affects no decision.
- **Components.** Amended by [D47](0047-control-plane-structure.md): the control plane's components are the compiler, planner, run driver, reconciler, scheduler and dispatcher, with the catalog, cache index, provenance, policy and plugin registry as services. Postgres is its only stateful dependency.
