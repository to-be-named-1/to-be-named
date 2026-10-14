// Task execution: a ready task run through admission, an attempt on an agent and advancement (D43, D47, D48).

dynamic platform.controlPlane "dynamic-task-execution" "A ready task run through admission, an attempt run by an agent, and the advancement of its run; the commit has its own view." {
    platform.controlPlane.runDriver -> platform.controlPlane.cacheIndex "Makes the authoritative cache lookup; no hit"
    platform.controlPlane.runDriver -> platform.controlPlane.scheduler "Hands over the ready task run"
    platform.controlPlane.scheduler -> platform.database "Admits it under fair share and takes its write leases"
    platform.controlPlane.scheduler -> platform.controlPlane.dispatcher "Hands over the admitted work"
    platform.controlPlane.dispatcher -> platform.controlPlane.runDriver "Creates the attempt, persisted before it is offered"
    platform.agent -> platform.controlPlane.agentGateway "Holds a long-poll for work"
    platform.controlPlane.dispatcher -> platform.controlPlane.agentGateway "Puts the offer on a waiting long-poll"
    platform.controlPlane.agentGateway -> platform.agent "Returns the offer on the long-poll"
    platform.agent -> platform.controlPlane.agentGateway "Claims the attempt"
    platform.agent -> kubernetes "Launches the unit"
    platform.unitRuntime -> platform.agent "Sends events, then the end of the attempt"
    platform.agent -> platform.controlPlane.agentGateway "Renews the lease with heartbeats, then reports the end"
    platform.controlPlane.agentGateway -> platform.controlPlane.dispatcher "Passes the report on"
    platform.controlPlane.dispatcher -> platform.controlPlane.runDriver "Reports the outcome"
    platform.controlPlane.runDriver -> platform.database "Updates the successors' readiness, and ends the run when every task run has ended"
    autoLayout lr
}
