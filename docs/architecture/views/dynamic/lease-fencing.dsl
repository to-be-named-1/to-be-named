// Lease fencing: a pool cut off from a running control plane loses its attempt; idempotency keys protect side effects,
// fencing rejects the late commit, and the stop set ends the stale unit (D40, D48, D64).

dynamic platform.controlPlane "dynamic-lease-fencing" "A pool cut off from a running control plane loses its attempt: the retry runs once the pool reconnects, task-run idempotency keys keep side effects from repeating, fencing rejects the late commit, and the stop set ends the stale unit. A single replica that falls silent loses nothing, since the pool's other replicas adopt its attempts." {
    platform.agent -> platform.controlPlane.agentGateway "The pool loses its network to the control plane, which keeps running; no replica's heartbeats arrive, and the unit keeps running"
    platform.unitRuntime -> platform.agent "Before a side effect, the stale unit asks its owner to confirm that its attempt is current; the check cannot be made, so the side effect pauses"
    platform.controlPlane.dispatcher -> platform.controlPlane.runDriver "The lease expired: reports the attempt lost"
    platform.controlPlane.runDriver -> platform.database "Records it lost in an epoch-fenced transaction, applies the retry budget and creates the next attempt"
    platform.controlPlane.runDriver -> platform.controlPlane.scheduler "The retry is ready"
    platform.agent -> platform.controlPlane.agentGateway "The pool reconnects, and the old attempt's owner resends the commit request it holds"
    platform.controlPlane.agentGateway -> platform.controlPlane.dispatcher "Passes it on"
    platform.controlPlane.dispatcher -> platform.controlPlane.runDriver "Checks the fencing token: the attempt is no longer current"
    platform.controlPlane.agentGateway -> platform.agent "Answers fenced"
    platform.agent -> platform.controlPlane.agentGateway "The owner's heartbeat lists the old attempt"
    platform.controlPlane.agentGateway -> platform.agent "The stop set names it; the replica stops the unit, and its staged files are left for collection"
    platform.agent -> platform.controlPlane.agentGateway "A replica claims the retry"
    platform.unitRuntime -> sideEffectTargets "The retry learns the stale attempt's intent and writes with an idempotency key derived from the task run, so what the stale attempt already wrote is not repeated"
    autoLayout lr
}
