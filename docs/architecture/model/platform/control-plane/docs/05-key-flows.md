## Key flows

Each flow below is a dynamic view whose steps are numbered on the diagram. The text adds what a diagram cannot show: which steps share a transaction, what is fenced and by what, and why.

### Run start

![](embed:dynamic-run-start)

The reconciler finds the due schedule by claiming its work row, on any worker replica. The run is created idempotently: a unique constraint on workflow, trigger and logical interval makes a repeated firing harmless ([D47]({workspace}/decisions/Platform#47)). External inputs are fixed first, by source probes, and internal inputs are then resolved in one repeatable-read transaction, so that the versions a run reads are consistent with each other ([D14]({workspace}/decisions/Platform#14), [D42]({workspace}/decisions/Platform#42), [D49]({workspace}/decisions/Platform#49)). The planner is a pure function that receives every input from the run driver; it shows expected reuse and binds nothing ([D8]({workspace}/decisions/Platform#8), [D47]({workspace}/decisions/Platform#47)). Recording the run, its plan and its first task runs is one of the [transactions across contexts](03-components.md#3.11).

### Source probe

![](embed:dynamic-source-probe)

The control plane never contacts a data source, so a probe unit in the data plane fixes each external source's version or position at run start, without reading data ([D40]({workspace}/decisions/Platform#40), [D49]({workspace}/decisions/Platform#49)). Probes are batched per pool and offered like any other work. The probed positions are recorded together with the resolved internal inputs, so that all of a run's inputs are fixed at one point, and each source's last probed position is kept.

### Task execution

![](embed:dynamic-task-execution)

The authoritative cache lookup is made when the task run is created; a hit records the outcome reused, and the task run is never queued ([D8]({workspace}/decisions/Platform#8), [D47]({workspace}/decisions/Platform#47)). Admission takes the task run's write leases, so two writers of a partition never run at once ([D43]({workspace}/decisions/Platform#43), [D48]({workspace}/decisions/Platform#48)). The dispatcher creates the attempt through the run driver, following the [attempt lifecycle](03-components.md#3.10), and persists it before it is offered, so a failover never loses an offer ([D48]({workspace}/decisions/Platform#48)). Heartbeats renew the lease in the leader's memory. The end report advances the run in the transaction that records the outcome, by decrementing each successor's count of pending upstream task runs ([D47]({workspace}/decisions/Platform#47)).

### Data commit

![](embed:dynamic-data-commit)

The fencing check, the write-lease check and the catalog's commit form one transaction, taking locks in the order set for [transactions across contexts](03-components.md#3.11) ([D15]({workspace}/decisions/Platform#15), [D42]({workspace}/decisions/Platform#42), [D48]({workspace}/decisions/Platform#48)). The commit writes one outbox row for each subscribed handler in the same transaction; projection, reconciler wake-ups and every other consequence follow from those rows, which keeps the commit path short ([D42]({workspace}/decisions/Platform#42), [D48]({workspace}/decisions/Platform#48)). Commit requests are idempotent by attempt and request identifier, so a replayed request receives the same answer, committed or fenced ([D40]({workspace}/decisions/Platform#40)).

### Lease fencing

![](embed:dynamic-lease-fencing)

A stale attempt is stopped from doing harm in three ways, one for each kind of effect. Against repeated side effects, a side-effecting step first confirms its lease, so it pauses while its agent replica is cut off, and writes with an idempotency key derived from the task run rather than the attempt, so the retry does not repeat what the stale attempt wrote ([D40]({workspace}/decisions/Platform#40)). Against a late commit, the fencing token stops the stale attempt's buffered commit: the run driver records the attempt lost in an epoch-fenced transaction, and from then on only the retry is current ([D47]({workspace}/decisions/Platform#47), [D48]({workspace}/decisions/Platform#48)). Against wasted work, the stop set in the replica's next renewal response ends the stale unit, whose staged files are left for collection ([D48]({workspace}/decisions/Platform#48)).

### Leader failover

![](embed:dynamic-leader-failover)

The leader's advisory lock is held by a session on a dedicated connection made directly to Postgres, so it is released when that session ends. The standby that takes the lock increments the epoch and makes no leader-only write until one transaction timeout and a margin have passed, by which time the old leader's transactions have finished or been ended ([D47]({workspace}/decisions/Platform#47)). It then rebuilds its [hot state](04-state.md#4.2) and treats every active attempt as renewed. Only after that does it open the agent port, and agents' retries reach it as described under [routing to roles](06-failure-and-scaling.md#6.5). To the rest of the system a failover is a control-plane restart, to which the grace period applies ([D40]({workspace}/decisions/Platform#40), [D43]({workspace}/decisions/Platform#43)).
