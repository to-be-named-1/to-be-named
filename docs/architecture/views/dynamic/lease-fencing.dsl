// Lease fencing: a partitioned agent replica loses its attempt; idempotency keys protect side effects, fencing rejects
// the late commit, and the stop set ends the stale unit (D40, D48).

dynamic platform.controlPlane "dynamic-lease-fencing" "A partitioned agent replica loses its attempt: the retry runs on another replica, task-run idempotency keys keep side effects from repeating, fencing rejects the buffered late commit, and the stop set ends the stale unit." {
    platform.agent -> platform.controlPlane.agentGateway "The partitioned replica's heartbeats stop arriving; its unit keeps running"
    platform.unitRuntime -> platform.agent "Before a side effect, the stale unit asks to confirm its lease; the check fails, so the side effect pauses"
    platform.controlPlane.dispatcher -> platform.controlPlane.runDriver "The lease expired: reports the attempt lost"
    platform.controlPlane.runDriver -> platform.database "Records it lost in an epoch-fenced transaction, applies the retry budget and creates the next attempt"
    platform.controlPlane.runDriver -> platform.controlPlane.scheduler "The retry is ready"
    platform.agent -> platform.controlPlane.agentGateway "Another replica claims the retry"
    platform.unitRuntime -> sideEffectTargets "The retry writes with an idempotency key derived from the task run, so what the stale attempt already wrote is not repeated"
    platform.agent -> platform.controlPlane.agentGateway "The partitioned replica reconnects and resends the commit request it buffered"
    platform.controlPlane.agentGateway -> platform.controlPlane.dispatcher "Passes it on"
    platform.controlPlane.dispatcher -> platform.controlPlane.runDriver "Checks the fencing token: the attempt is no longer current"
    platform.controlPlane.agentGateway -> platform.agent "Answers fenced"
    platform.agent -> platform.controlPlane.agentGateway "The replica's heartbeat lists the old attempt"
    platform.controlPlane.agentGateway -> platform.agent "The stop set names it; the replica stops the unit, and its staged files are left for collection"
    autoLayout lr
}
