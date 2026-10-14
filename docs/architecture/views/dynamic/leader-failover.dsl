// Leader failover: a standby takes leadership, waits out the old leader's transactions and rebuilds hot state (D47, D48).

dynamic platform.controlPlane "dynamic-leader-failover" "A standby takes over leadership, waits out the old leader's transactions, rebuilds hot state from Postgres and treats active leases as renewed." {
    platform.controlPlane.leadership -> platform.database "The old leader's session ends, releasing the advisory lock"
    platform.controlPlane.leadership -> platform.database "A standby takes the lock and increments the epoch"
    platform.controlPlane.leadership -> platform.controlPlane.scheduler "After one transaction timeout and a margin, starts the leader loops"
    platform.controlPlane.scheduler -> platform.database "Rebuilds the queues and fair-share usage"
    platform.controlPlane.leadership -> platform.controlPlane.runDriver "Starts advancing runs from agents' reports on the new leader"
    platform.controlPlane.runDriver -> platform.database "Recounts the map-group and outstanding task-run counts lost with the old leader"
    platform.controlPlane.leadership -> platform.controlPlane.dispatcher "Starts dispatch"
    platform.controlPlane.dispatcher -> platform.controlPlane.runDriver "Loads the active attempts; each is treated as renewed"
    platform.controlPlane.leadership -> platform.controlPlane.agentGateway "Opens the agent port"
    platform.agent -> platform.controlPlane.agentGateway "Agents' retries reach the new leader; heartbeats resume"
    autoLayout lr
}
