# 20. Backfill commits and scheduling

Date: 2026-10-11
Applies to: platform.controlPlane, operator

## Status

Accepted

Amended by [43. Scheduling and capacity](0043-scheduling-and-capacity.md)
Amended by [48. Execution mechanics](0048-execution-mechanics.md)

## Context

The reasoning on the platform as the queue, in [D43](0043-scheduling-and-capacity.md), also cites this decision.

## Decision

A backfill commits each logical interval as it completes, while downstream reconciliation is deferred and planned once over everything the backfill changed. Restatements may instead be committed atomically. Backfills run at lower priority than scheduled work.

- **Scope.** These are data commits in the platform catalog ([D15](0015-atomic-publication.md)), not version-control commits of workflow definitions. Each data snapshot nevertheless records the definition version that produced it.
- **Per interval.** By default each interval is committed when it finishes, so progress is visible, a failure affects only its own interval, and the backfill resumes from the first incomplete interval.
- **Coalescing.** While a backfill runs, the reconciler holds downstream work and plans it once — when the backfill completes, or at batch boundaries for long backfills — over the union of changed partitions. Without this, a lateness window causes each downstream partition to be rebuilt several times.
- **Restatement.** A backfill that recomputes existing partitions with changed logic may be declared atomic: every interval is staged and a single snapshot is committed at the end, so consumers never observe a mixture of old and new logic. Gap-filling backfills do not need this.
- **Restatement conflicts.** Amended by [D48](0048-execution-mechanics.md): staging units hold write leases only while they run. The final commit takes every lease at once and checks that no partition it replaces was committed after its interval was staged; conflicting intervals are re-staged before the commit.
- **History.** Commits made by one backfill carry its identifier, so version history presents the backfill as a single collapsible entry.
- **Priority.** Backfills run below scheduled runs under fair scheduling ([CORE 3.6]({workspace}/documentation#3)), so a long backfill never delays current pipelines. Writes to the same partition are serialized, so a backfill and a scheduled run cannot collide. Amended by [D43](0043-scheduling-and-capacity.md): backfills are admitted only to idle capacity and production work never queues behind waiting backfill work, but a running backfill attempt is not stopped by default, so production work may wait for it to finish unless the pool enables preemption; serialization of writes is by partition write leases taken at admission.
