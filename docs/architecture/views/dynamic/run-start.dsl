// Run start: a scheduled run from its trigger to the transaction that records it (D14, D47, D49).

dynamic platform.controlPlane "dynamic-run-start" "A scheduled run from its trigger to the transaction that records the run, its plan and its first task runs." {
    platform.controlPlane.reconciler -> platform.database "Claims the due schedule's work row"
    platform.controlPlane.reconciler -> platform.controlPlane.runDriver "Creates the run for the logical interval, idempotently"
    platform.controlPlane.runDriver -> platform.controlPlane.probeScheduling "Requests probes for the external inputs; the run stays resolving"
    platform.controlPlane.probeScheduling -> platform.controlPlane.runDriver "Wakes the run with the probed positions"
    platform.controlPlane.runDriver -> platform.controlPlane.catalog "Resolves the internal inputs in one repeatable-read transaction"
    platform.controlPlane.runDriver -> platform.controlPlane.planner "Plans the run"
    platform.controlPlane.planner -> platform.controlPlane.authorization "Checks access under the run's project identity"
    platform.controlPlane.planner -> platform.controlPlane.cacheIndex "Computes expected reuse"
    platform.controlPlane.runDriver -> platform.database "Records the run, its plan and its first task runs in one transaction"
    autoLayout lr
}
