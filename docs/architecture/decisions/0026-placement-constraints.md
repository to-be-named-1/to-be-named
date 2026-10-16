# 26. Placement constraints

Date: 2026-10-11
Applies to: platform.controlPlane, platform.agent

## Status

Accepted

## Context

**Placement constraints deferred, with three seams kept** (D26). Constraints can be added later as additive changes, but the location of past attempts and artifacts cannot be reconstructed, so it is recorded from the first release. Cache hits pass through an eligibility filter, and the planner decides every placement explicitly. Ideas discussed but not decided are recorded in D26 under "Considered".

## Decision

Placement constraints, the hard requirements and soft preferences that govern where an execution unit runs, are deferred from the first release. Until they are introduced, the planner places units by the rules of [D25](0025-processing-engines-and-runtimes.md) alone, and the hard-constraint step of its selection precedence is empty. Three requirements are kept from the outset so that constraints can be added later without rework and without losing the ability to judge historical runs and data against them.

- **Deferred.** An optional block of placement requirements and preferences in the IR; residency and data-movement rules declared on datasets; resolution of constraints by the planner, with rejection of plans whose hard constraints cannot all be met; and handling of units whose constraints cannot be met by currently available capacity.
- **Seam 1.** **Location record.** Every attempt records the backend and region in which it ran, and every artifact manifest records a storage location specific enough to identify its region ([D23](0023-artifact-storage-layout.md)). This record cannot be reconstructed afterwards: without it, artifacts produced before constraints exist could not be judged against a residency rule introduced later and would all have to be treated as ineligible.
- **Seam 2.** **Cache eligibility.** A cache lookup finds a candidate under its key and then applies eligibility checks before the output is reused. The permission check of [D9](0009-cache-scope.md) is the first such check; a placement check is later added as a further check without changing the cache.
- **Seam 3.** **Explicit placement.** The planner decides every unit's backend and location and records the reason ([D25](0025-processing-engines-and-runtimes.md)), including where the reason is only the default. No backend selects a location that the planner cannot see or override.
- **Considered.** Discussed before deferral and not decided: deriving most hard constraints from the policy of the datasets a unit reads rather than requiring node authors to declare them; limiting node-level requirements to properties of the computation, such as an accelerator or a tool licensed on one cluster; expressing requirements in the IR as abstract labels resolved through environment bindings rather than as concrete regions; and treating a cached output stored in a location that violates a run's constraints as a miss.
- **Transition.** Workflows built before constraints exist may depend on unrestricted data movement and fail to plan once constraints apply. A warning-only phase before enforcement was raised as the likely remedy and is not decided.
- **Open items.** [S6]({workspace}/documentation#3) and [S23]({workspace}/documentation#3) remain open and are deferred with this decision.

## Follow-ups

- Placement constraints and residency: the IR block, dataset-level rules, constraint resolution, capacity conflicts, and the transition for existing workflows (a warning-only phase was suggested). The "Considered" ideas await a decision.
