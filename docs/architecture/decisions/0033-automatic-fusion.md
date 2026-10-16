# 33. Automatic fusion

Date: 2026-10-11
Applies to: platform.controlPlane

## Status

Accepted

Amends [1. Node granularity](0001-node-granularity.md)
Amended by [46. Control-flow constructs](0046-control-flow-constructs.md)
Amended by [50. Development mode](0050-development-mode.md)

## Context

**Fully automatic fusion from the start** (D33). Manual-first sequencing was rejected: with a canvas of fine-grained nodes, every built-in node would become its own unit, the costly case in the fusion example. Legality is deterministic and needs no measurements; only a cost-informed policy does, so the policy is replaceable. Using composites as the manual fusion control was rejected because composition is a canvas convenience, not an execution concept.

As first recorded, runs on samples always executed unfused, retaining every intermediate ([CORE 6.6]({workspace}/documentation#3)).

## Decision

Fusion is fully automatic from the first slice. The planner separates **legality** — whether nodes may share a unit — from **policy** — which of the legal groupings to choose.

- **Composition is separate.** Composites are flattened before fusion is planned. A composite may become one unit, several units, or part of a unit shared with nodes outside it; composition never implies fusion.
- **Legality.** The fusion conditions in the [vocabulary]({workspace}/documentation#2): a shared image and execution location ([D32](0032-execution-unit-structure.md)), compatible resources, no control flow between the nodes, no output that must be stored, no external side effect, no node marked to run as its own unit, and no cycle between units. Legality is deterministic and needs no run-time measurements. Amended by [D46](0046-control-flow-constructs.md): a loop whose execution mode is in-unit runs its body and all its iterations inside one unit, provided the body could itself be fused.
- **Policy.** Behind a replaceable interface. The first-slice policy fuses as far as legality allows, subject to guard rails: a unit's resource request may not exceed a configurable ceiling, and independent branches are not fused where doing so would give up their parallelism across machines. Later policies may use measured cost and change frequency from run history.
- **Manual control.** Users can only split: pin a cache boundary, or mark a node to run as its own unit ([CORE 2.13]({workspace}/documentation#3)). A manual control to fuse would add nothing, since the policy already fuses wherever fusion is legal.
- **Determinism.** The same IR under the same policy version always yields the same units, and every plan records the policy version, which plan pinning ([D28](0028-warehouse-connection-policy-and-plan-pinning.md)) and reproducible plans rely on. Because cache keys are chained through nodes ([D8](0008-cache-keying.md)), a change of policy does not invalidate cached outputs.
- **Development runs.** Amended by [D50](0050-development-mode.md): a development run chooses its fusion mode, automatic (the policy and the author's splits) or unfused, and separately how many intermediates to keep: none, statistics and samples, or full. Sample runs default to automatic fusion with full intermediates and full-scale development runs to automatic fusion with statistics and samples.

## Follow-ups

- A cost-informed fusion policy using measured cost and change frequency from run history.
