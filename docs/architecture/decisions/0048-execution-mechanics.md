# 48. Execution mechanics

Date: 2026-10-11
Applies to: platform.controlPlane, platform.database, platform.agent

## Status

Accepted

Amends [15. Atomic publication](0015-atomic-publication.md)
Amends [20. Backfill commits and scheduling](0020-backfill-commits-and-scheduling.md)
Amends [31. Execution state model](0031-execution-state-model.md)
Amends [40. Protocol between the control and data planes](0040-protocol-between-the-control-and-data-planes.md)
Amends [42. Catalog persistence](0042-catalog-persistence.md)
Amends [43. Scheduling and capacity](0043-scheduling-and-capacity.md)
Amended by [50. Development mode](0050-development-mode.md)

## Context

**Lease renewals in memory** (D48). Persisting renewals would write a row for every running attempt at every heartbeat. Because [D40](0040-protocol-between-the-control-and-data-planes.md) already grants every lease a grace period after a restart, a new leader can treat all active leases as renewed and lose nothing.

**Write leases held by the task run** (D48). Held by the attempt, a lease would be released during a retry's back-off and let another run's writer take the partition, against the overlap policy of [CORE 3.7]({workspace}/documentation#3). An atomic restatement does not hold the leases of every interval for its whole length, which would contradict the backfill guarantee of [D43](0043-scheduling-and-capacity.md); it checks for conflicting commits at its final commit and re-stages those intervals.

**One outbox row per handler** (D48). A relay fanning each event out into delivery rows after commit added a hop, a table and more writes than writing one row per subscribed handler in the producing transaction. One row per event shared by all handlers would let one failing handler block the others, and per-handler cursors over the outbox are the high-water mark rejected in [D42](0042-catalog-persistence.md). River, pgmq and Watermill were rejected because their tables carry no tenant or row-level security ([D45](0045-isolation-enforcement-and-role-model.md)), and change data capture because it adds a component and logical replication on the customer's Postgres.

## Decision

How leases are renewed and ended, how commits are fenced, how write leases are held, how the state machines of [D31](0031-execution-state-model.md) are encoded, and how events reach their handlers.

- **Lease renewals.** The leader holds each lease's last renewal in memory, timed by its monotonic clock; Postgres records only the grant, as the attempt row, and the end. A new leader treats every active attempt as renewed at takeover, which is the grace period of [D40](0040-protocol-between-the-control-and-data-planes.md), so nothing is lost by not persisting renewals. Persisting them would write a row for every running attempt at every heartbeat.
- **Offers and claims.** An attempt row is committed before the attempt is offered on any long-poll, so a failover never loses an attempt an agent is running. An offer not claimed within a timeout is offered again, and a claim is a conditional update on the attempt that only one replica can win.
- **Stop set.** A heartbeat lists the attempts the agent is renewing; the response lists those the control plane no longer recognizes — lost, fenced, canceled or superseded — and the agent stops them, so orphaned containers stop within one heartbeat rather than at the hard limit.
- **Lost attempts.** When a lease expires, the leader records the attempt's end with the outcome lost in an epoch-fenced transaction ([D47](0047-control-plane-structure.md)), and the run driver applies the platform retry budget ([D31](0031-execution-state-model.md)).
- **Sequence numbers.** A state-bearing message numbered at or below the last one applied receives the recorded answer; the next number is applied; anything further ahead is refused and resent ([D40](0040-protocol-between-the-control-and-data-planes.md)).
- **Fencing token.** The task run and its attempt number. A commit, or a checkpoint commit, locks the task-run row and requires the attempt to be current and not ended. Staging is scoped to the attempt ([D15](0015-atomic-publication.md)), so object storage needs no fencing.
- **Write leases.** A write lease is held by the task run while it is active, including retry back-off, and released when it ends or suspends; a resumed task run takes its leases again at admission. A commit requires leases covering every partition it writes. A unit whose output partitions are discovered at run time ([D13](0013-partitioning-intervals-and-dataset-ownership.md)) takes a lease on the whole dataset; each append to an open partition, and marking it complete, takes that partition's lease. Holding the lease by the attempt was rejected: during a retry's back-off another run's writer could take the partition, against the overlap policy of [CORE 3.7]({workspace}/documentation#3).
- **Overlap.** By default runs of a workflow may overlap, including runs for the same interval, serialized per partition by write leases; preventing or queueing overlap is set per workflow ([CORE 3.7]({workspace}/documentation#3)).
- **Atomic restatements.** Staging units hold write leases only while they run. The final commit takes every lease at once and checks that no partition it replaces was committed after its interval was staged; conflicting intervals are re-staged and then committed. Holding every interval's lease for the whole restatement was rejected because it contradicts the backfill guarantee of [D43](0043-scheduling-and-capacity.md), and committing over newer data regardless because it would silently overwrite that data ([D20](0020-backfill-commits-and-scheduling.md)).
- **State encoding.** Phase, sub-state and outcome are columns. Check constraints keep the outcome empty until the phase is ended and each sub-state within its phase; every transition is a conditional update on the expected state; and the transition table is defined once in Go, which generates validation, documentation and tests. History is kept as timestamp columns for each key transition, with each attempt its own row and user actions audited, which gives queue time against run time ([CORE 4.3]({workspace}/documentation#3)). A generic transition log was rejected because it would double the writes at the transition rates of [D43](0043-scheduling-and-capacity.md), and event sourcing because rebuilding a run of a million task runs from events offers nothing the rows do not.
- **Sub-states.** A run is pending while waiting for inputs, resolving or planning; active while running, draining or canceling; and suspended when paused. A task run is pending while blocked or ready; active while attempting or backing off; and suspended for an approval or a gate hold. An attempt is pending when offered and active while starting, running or committing.
- **Held attempts.** An attempt whose commit awaits a quality-gate release or an approval ends with the outcome **held**. Its staged manifest stays durable, and the control plane completes the commit later, on release or approval, fenced by the task run ([D15](0015-atomic-publication.md), [D31](0031-execution-state-model.md)). A failure class for failed gates was rejected because approvals are not failures.
- **Outbox rows.** A transaction that produces an event writes one outbox row for each handler subscribed to it, looked up in a registry compiled into the binary; conditional subscriptions write a row only where a handler applies, such as projection for a projected dataset. A row carries the tenant, event type, handler, aggregate identifier, ordering key, aggregate version, payload, state, attempt count, next attempt time and last error. The table is keyed by tenant, under forced row-level security and partitioned by time ([D45](0045-isolation-enforcement-and-role-model.md)).
- **Delivery.** Workers on any replica claim due rows with `FOR UPDATE SKIP LOCKED`. Where a handler declares an ordering key, one row per key is in flight at a time, lowest aggregate version first, never by outbox identifier, which is assigned before commit ([D42](0042-catalog-persistence.md)). A handler runs in a transaction scoped to the row's tenant and completes its row in the same transaction, so effects in Postgres happen once and external effects rely on idempotency keys. Failures retry with back-off and jitter; a row that exhausts its attempts becomes a dead letter, which raises an alert and can be re-driven. Rows are removed by dropping time partitions, and lag, the age of the oldest undelivered row and dead letters are exported as metrics. The claim, retry and dead-letter code is shared with the reconciler's work rows and probe scheduling ([D47](0047-control-plane-structure.md), [D49](0049-source-probes.md)).
- **Wake-ups.** In-process where producer and consumer share a process; otherwise by NOTIFY, sent after commit, outside the transaction and batched; polling remains the guarantee. NOTIFY is never sent from commit or transition transactions: a transaction that has issued NOTIFY takes a database-wide lock at commit, which serializes such commits, as reported for the PostgreSQL versions the platform supports ([D44](0044-minimum-technology-stack.md)). The leader is one consumer of events that make work ready, so approvals and releases recorded on other replicas reach its queue. Telemetry stays outside the outbox ([D21](0021-architecture-planes.md)).
- **Amends.** [D15](0015-atomic-publication.md): the fencing token is the task run and attempt number, and a commit requires covering write leases. [D20](0020-backfill-commits-and-scheduling.md): an atomic restatement checks for conflicting commits at its final commit and re-stages those intervals. [D31](0031-execution-state-model.md): attempts gain the outcome held, and sub-states are fixed. [D40](0040-protocol-between-the-control-and-data-planes.md): renewals are held in memory, attempts are persisted before they are offered, and renewal responses carry a stop set. [D42](0042-catalog-persistence.md): a commit writes one outbox row per subscribed handler. [D43](0043-scheduling-and-capacity.md): write leases are held by the task run, a dataset-wide lease covers partitions discovered at run time, and overlap is allowed by default.
- **Lines.** Amended by [D50](0050-development-mode.md): write leases are keyed by dataset, line and partition, outbox rows carry the line, and each handler declares the lines it serves.

## Rejected alternatives

- One row per event shared by all handlers, under which a failing handler blocks the others.
- A relay fanning events out into delivery rows after commit, which adds a hop, a table and writes.
- Per-handler status on one row, or per-handler cursors over the outbox, which bring contention or the high-water mark ruled out by [D42](0042-catalog-persistence.md).
- River, pgmq and Watermill, whose tables carry no tenant or row-level security ([D45](0045-isolation-enforcement-and-role-model.md)), River also inserting in batches with `COPY FROM` and running a second leader election.
- Change data capture from the write-ahead log, which needs logical replication and another component.

## Follow-ups

- Defaults for the offer timeout, the delivery attempts before a dead letter and their back-off; how many times a restatement re-stages conflicting intervals before reporting them.
