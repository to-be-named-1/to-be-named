# 54. Domain-driven design

Date: 2026-10-16
Applies to: platform

## Status

Accepted

## Context

The platform's domain is large and dense in concepts: workflows and their versions, datasets, versions and partitions, runs, task runs and attempts, leases, pools and capacity domains. The control plane is one binary that must stay modular as it grows, and boundaries between contexts keep a later split into services possible without redesign. The control plane was already designed this way in [D47](0047-control-plane-structure.md) and [D48](0048-execution-mechanics.md), but the approach was never stated as the one all design follows.

## Decision

The platform is designed by domain-driven design.

- **Own domain model.** The domain model is the platform's own; no external engine's model becomes it ([D3](0003-ir-and-execution-engines.md)).
- **Bounded contexts.** Every capability belongs to a bounded context, or justifies a new one. Each context owns its tables and its package tree; its first application is the control plane's eight contexts ([D47](0047-control-plane-structure.md)).
- **Aggregates.** Invariants belong to aggregates and are enforced in the database, by row locks, conditional updates and unique constraints ([D47](0047-control-plane-structure.md)).
- **Integration.** Contexts integrate through each other's interfaces and through domain events delivered by the outbox, never through shared tables ([D47](0047-control-plane-structure.md), [D48](0048-execution-mechanics.md)).
- **Anti-corruption layers.** External models are translated at the edges: the IR toward engines and backends ([D3](0003-ir-and-execution-engines.md)), and the separately versioned contracts of the agent protocol ([D40](0040-protocol-between-the-control-and-data-planes.md)).
- **Ubiquitous language.** The terms of the [vocabulary]({workspace}/documentation#2) are used unchanged in the code, the model and the documentation.
