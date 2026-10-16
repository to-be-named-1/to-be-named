## Runtime view

The flows inside the control plane, from run start and source probes to task execution, data commits, lease fencing and leader failover, are dynamic views of its components, explained in the [control-plane key flows]({workspace}/documentation/Platform/Control-plane%20server#5). This section holds the flows that cross containers.

### Sample run

![](embed:dynamic-sample-run)

A preview from the canvas starts a sample run of the node being edited, on a snapshot of the draft ([D50]({workspace}/decisions/Platform#50)). The planner samples the inputs at the selection boundary and bounds every read by the author's clearance, and the run's work is scheduled in the interactive class ([D43]({workspace}/decisions/Platform#43), [D50]({workspace}/decisions/Platform#50)). The sample is built by referential subsetting in a sample-building unit and stored under the input versions and the sample specification, so a later preview on the same inputs finds it in the cache index and goes straight to the node. The node runs in the author's session unit, a warm container that starts a fresh process for each unit, so its result never differs from a fresh container's; the run writes only run-scoped artifacts ([D50]({workspace}/decisions/Platform#50)). How the canvas shows the results is open item [S3]({workspace}/documentation#7.3).
