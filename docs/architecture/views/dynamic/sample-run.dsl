// Sample run: a preview from the canvas, its sample built once and the node run in the author's session (D50).

dynamic platform "dynamic-sample-run" "A preview from the canvas: a sample run of the node being edited, its sample built at the selection boundary and the node run in the author's session." {
    workflowAuthor -> platform.webApp "Previews the node being edited"
    platform.webApp -> platform.controlPlane "Starts a sample run of the node from a snapshot of the draft"
    platform.controlPlane -> platform.database "Records the run, its selection sampled at the boundary and its reads bounded by the author's clearance"
    platform.agent -> platform.controlPlane "Holds a long-poll for work"
    platform.controlPlane -> platform.agent "Offers the sample-building attempt, in the interactive class"
    platform.agent -> kubernetes "Launches the sample-building unit"
    platform.sampleBuilder -> platform.agent "Fetches its specification"
    platform.sampleBuilder -> objectStorage "Samples the driving input, keeps the matching rows of every input joined to it, and stores the sample"
    platform.sampleBuilder -> platform.agent "Reports the stored sample"
    platform.agent -> platform.controlPlane "Reports the end; the node's task run becomes ready"
    platform.controlPlane -> platform.agent "Offers the node's attempt, naming the author's session"
    platform.sessionUnit -> platform.agent "Takes the unit specification and runs it in a fresh process"
    platform.sessionUnit -> objectStorage "Reads the sample and writes run-scoped artifacts"
    platform.sessionUnit -> platform.agent "Sends events, then the end of the attempt"
    platform.agent -> platform.controlPlane "Reports the end; the run ends"
    autoLayout lr
}
