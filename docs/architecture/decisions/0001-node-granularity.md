# 1. Node granularity

Date: 2026-10-11
Applies to: platform.webApp, platform.controlPlane

## Status

Accepted

Amended by [33. Automatic fusion](0033-automatic-fusion.md)

## Context

As first recorded, this decision sequenced fusion: manual fusion first, by marking a composite "run as one unit", and automatic fusion later. [D33](0033-automatic-fusion.md) withdrew that sequencing.

## Decision

Granularity is chosen by context: fine-grained nodes where step-by-step control helps, coarse nodes where a whole script is the natural unit. Composition collapses large flows into a single node nested inside a workflow.

- **Follows.** Nodes and execution units are separate concepts; the canvas node is not the unit of dispatch.
- **Follows.** Fusion is applied automatically by the planner; users control it by splitting ([D33](0033-automatic-fusion.md)).
- **Sequencing.** Node and execution unit are separate in the IR from the outset. Amended by [D33](0033-automatic-fusion.md): fusion is fully automatic from the first slice, behind a replaceable policy, and composites play no part in it. Users can pin a cache boundary inside a fused chain or mark a node to run as its own unit.
