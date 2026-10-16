# 2. Graph model

Date: 2026-10-11
Applies to: platform.webApp, platform.controlPlane

## Status

Accepted

Amended by [41. IR text form, round-trip and structure](0041-ir-text-form-round-trip-and-structure.md)
Amended by [46. Control-flow constructs](0046-control-flow-constructs.md)

## Context

The reasoning on two levels of iteration and on loops that are always bounded, in [D46](0046-control-flow-constructs.md), extends the constructs of this decision.

## Decision

Workflows are control-flow graphs, not strictly DAGs. Conditionals, loops and adaptive iteration are supported.

- **Structured.** Only structured constructs are permitted — if/else, map, and bounded loops with a maximum iteration count — and no arbitrary back-edges, so definitions remain statically analyzable.
- **Unrolled trace.** Each loop iteration unrolls into distinct task runs at execution, so the run trace is always acyclic and provenance and caching operate on it unchanged. Amended by [D46](0046-control-flow-constructs.md): a loop may instead run inside one unit, its iterations recorded within one task run; carried state, branch joins and an n-way switch join the structured constructs.
- **Run conditions.** Amended by [D41](0041-ir-text-form-round-trip-and-structure.md): each node also carries a run rule over the outcomes of its upstream nodes — all succeeded by default, all finished, any failed and similar — optionally combined with a condition. Conditions, collections and loop termination are CEL expressions evaluated by the control plane ([D41](0041-ir-text-form-round-trip-and-structure.md)).
