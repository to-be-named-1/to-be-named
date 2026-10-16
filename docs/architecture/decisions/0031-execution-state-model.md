# 31. Execution state model

Date: 2026-10-11
Applies to: platform.controlPlane, operator, datasetOwner

## Status

Accepted

Amended by [43. Scheduling and capacity](0043-scheduling-and-capacity.md)
Amended by [44. Minimum technology stack](0044-minimum-technology-stack.md)
Amended by [45. Isolation enforcement and role model](0045-isolation-enforcement-and-role-model.md)
Amended by [46. Control-flow constructs](0046-control-flow-constructs.md)
Amended by [47. Control-plane structure](0047-control-plane-structure.md)
Amended by [48. Execution mechanics](0048-execution-mechanics.md)
Amended by [50. Development mode](0050-development-mode.md)

## Context

**Phase separate from outcome** (D31). A single status enum tends to assume that every execution ends in success or failure, which [D12](0012-streaming-readiness.md) Seam 1 forbids. With a separate outcome, a long-lived execution simply never reaches the ended phase.

**Nested workflows inlined** (D31). A separate child run was rejected because it would resolve its inputs at a different instant from its parent and break the snapshot isolation of [D14](0014-input-version-resolution.md).

**Quality-gate holds are bounded** (D31). Indefinite suspension was rejected because [D14](0014-input-version-resolution.md) protects the resolved inputs of a run in progress, so an unresolved hold would pin storage indefinitely. A continuation after the timeout that reused the run's resolved inputs was also rejected, because those inputs are no longer protected once the run ends; a late override instead releases the quarantined version and lets downstream datasets be rebuilt on current data through normal staleness handling.

## Decision

Execution is recorded at three levels: the **run** (one execution of a workflow version for a trigger and a logical interval), the **task run** (one execution of a unit at an index path such as `map[17]` or `loop[3]/map[2]`) and the **attempt** (one try at a task run, holding the lease and fencing token).

- **Phase and outcome.** Each level carries a lifecycle phase — pending, active, suspended or ended — and, separately, an outcome that remains empty until the phase is ended. Finer states, such as a task run being ready, dispatched, running or committing, are sub-states within a phase. No level assumes that it will end, as [D12](0012-streaming-readiness.md) Seam 1 requires.
- **Outcomes.** A run ends succeeded, failed, canceled or skipped. A task run ends succeeded, failed, canceled, skipped or reused. An attempt ends committed, failed, lost, canceled or fenced. A conditional branch not taken ends as skipped with its reason. Degradation is not an outcome: it is a property of outputs and dataset versions ([D16](0016-input-readiness-and-degraded-outputs.md)).
- **Waiting for inputs.** A sub-state of the run's pending phase that precedes input resolution, holds no task runs and no compute, and is re-evaluated by the reconciler. When the wait times out, the readiness policy of [D16](0016-input-readiness-and-degraded-outputs.md) applies; by default a scheduled run then fails and alerts ([D14](0014-input-version-resolution.md), [D16](0016-input-readiness-and-degraded-outputs.md)).
- **Approval.** An approval node's task run enters a suspended state awaiting approval, holds no lease, and is resumed externally through the API. Gated publication uses the same state on its commit step, with the staged data held (CORE 6.8, MLE 3.4).
- **Approvals in development runs.** Amended by [D50](0050-development-mode.md): approval nodes in development runs are passed through as simulated, with a recorded note, unless the author chooses to pause at them; the run record carries the development fields of [D50](0050-development-mode.md).
- **Quality-gate hold.** A failed gate quarantines the staged data ([D15](0015-atomic-publication.md)), and downstream task runs are held rather than failed or retried (DE 4.4). The hold has a configurable timeout, after which the run ends as failed with the reason that an upstream gate failed. The timeout bounds how long [D14](0014-input-version-resolution.md)'s protection of resolved inputs can pin storage. Who may override is settled by [D45](0045-isolation-enforcement-and-role-model.md): the dataset's owner or a Maintainer of its project.
- **Override.** An override releases the quarantined version: it is an act on a dataset version, protected by the version's quarantine state, not a continuation of the run. Within the hold, the release commits the version and the held task runs resume in the same run, whose resolved inputs are still protected. After the timeout, the release is a publication act alone: no continuation run is started, the downstream datasets become stale because their upstream has a new version ([D13](0013-partitioning-intervals-and-dataset-ownership.md)), and they are rebuilt on current data by normal scheduling or a materialization request ([D24](0024-dataset-materialization-requests.md)) under each consumer's readiness policy ([D16](0016-input-readiness-and-degraded-outputs.md)). A released version older than the current version is recorded in history but does not become current. A quarantined version is retained until it is released, explicitly discarded or its quarantine retention expires, whose default belongs with [S15]({workspace}/documentation#3). Provenance records who released the version and when, its producing run and the gate verdict overridden; if that run's inputs are later collected, it decays to Traceable as any run would ([D7](0007-reproducibility-guarantee.md)). Re-executing the original run as recorded (CORE 2.16) remains available while its inputs are retained.
- **Failure classes.** An attempt that ends failed records a class: infrastructure, resource exhausted, timeout or task error. Infrastructure failures and lost attempts draw on a platform retry budget, separate from the author's retry policy, which governs task errors (CORE 2.5). A fenced attempt is not a failure: a newer attempt has superseded it. Resource exhaustion is a distinct class so that memory escalation ([S8]({workspace}/documentation#3)) can be added without a schema change. Health is derived from lease renewal ([D12](0012-streaming-readiness.md), Seam 2).
- **Checkpoint slot.** Every task run has an optional checkpoint slot, scoped to the task run rather than the attempt. A unit may write to it; its commits are fenced like any other; the next attempt receives the latest checkpoint. The platform does not interpret its contents, and provenance records when an attempt resumed from a checkpoint. This covers long-running training (MLE 2.3), resumption after reclamation of spot capacity (MLE 2.4) and resumption of a partially completed extraction (DE 1.5) without a separate task kind. Amended by [D46](0046-control-flow-constructs.md): a loop run inside one unit records its iterations within one task run and resumes from the last completed iteration through this slot.
- **Nested workflows.** A node that references another workflow is inlined into the parent run at compile time, pinned to a version of the referenced workflow, and each resulting task run records its origin so that the interface can group them. A separate child run would resolve its inputs at a different instant and break snapshot isolation ([D14](0014-input-version-resolution.md)).
- **Cache hits.** A unit served from cache is recorded as a task run with the outcome reused, a reference to the task run whose output was reused, and no attempts (CORE 2.13).
- **Pause and cancel.** Pausing stops dispatching new task runs and lets running attempts finish, after which the run is suspended until resumed; canceling signals running attempts at their next heartbeat (CORE 2.8). Amended by [D44](0044-minimum-technology-stack.md): the signal reaches the agent within about one round trip through its long-poll, and within one heartbeat at worst.
- **Deferred.** Whether the task runs of a large map are created up front or in batches as they are dispatched is settled with scheduler capacity ([S4]({workspace}/documentation#3)). Settled by [D43](0043-scheduling-and-capacity.md): in windows sized to the map's parallelism, tracked by a map-group record.
- **Held attempts and sub-states.** Amended by [D48](0048-execution-mechanics.md): an attempt whose commit awaits a quality-gate release or an approval ends with the outcome held, keeping its staged outputs durable, and the control plane completes the commit later, fenced by the task run. Sub-states are fixed: a run is pending while waiting for inputs, resolving or planning, active while running, draining or canceling, and suspended when paused; a task run is pending while blocked or ready, active while attempting or backing off, and suspended for an approval or a gate hold; an attempt is pending when offered and active while starting, running or committing.
- **Run outcome.** Amended by [D47](0047-control-plane-structure.md): a run fails if any of its task runs failed, unless the failure was consumed by a node whose run rule fires on failure ([D41](0041-ir-text-form-round-trip-and-structure.md)). The exact rule is settled with the IR specification.

## Follow-ups

- Default retention of quarantined versions ([S15]({workspace}/documentation#3)).
