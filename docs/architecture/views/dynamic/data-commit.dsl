// Data commit: staged outputs made current in one fenced transaction, then delivered to handlers (D15, D42, D48).

dynamic platform.controlPlane "dynamic-data-commit" "An attempt's staged outputs made current in one fenced transaction, and the events it produces delivered to their handlers." {
    platform.unitRuntime -> objectStorage "Stages outputs in the attempt's staging location"
    platform.unitRuntime -> platform.agent "Requests the commit"
    platform.agent -> platform.controlPlane.agentGateway "Sends the commit request with the fencing token"
    platform.controlPlane.agentGateway -> platform.controlPlane.dispatcher "Passes it on"
    platform.controlPlane.dispatcher -> platform.controlPlane.runDriver "Checks the fencing token: locks the task-run row; the attempt is current"
    platform.controlPlane.dispatcher -> platform.database "Checks the write leases"
    platform.controlPlane.dispatcher -> platform.controlPlane.catalog "Commits in the same transaction"
    platform.controlPlane.catalog -> platform.database "Records manifests, partition versions, the head move, read records and one outbox row per handler"
    platform.controlPlane.agentGateway -> platform.agent "Answers committed"
    platform.controlPlane.outbox -> platform.controlPlane.projectionScheduling "Delivers the commit event"
    platform.controlPlane.outbox -> platform.controlPlane.reconciler "Wakes the loops waiting on the dataset"
    autoLayout lr
}
