// Source probe: a run's external inputs fixed at run start by a probe unit in the data plane (D49).

dynamic platform.controlPlane "dynamic-source-probe" "A run's external inputs fixed at run start by a probe unit in the data plane, which returns versions and positions without reading data." {
    platform.controlPlane.runDriver -> platform.controlPlane.probeScheduling "Requests probes for the external inputs"
    platform.controlPlane.probeScheduling -> platform.database "Batches them per pool"
    platform.controlPlane.probeScheduling -> platform.controlPlane.dispatcher "Hands over the batch"
    platform.agent -> platform.controlPlane.agentGateway "Holds a long-poll for work"
    platform.controlPlane.dispatcher -> platform.controlPlane.agentGateway "Puts the probe on the waiting long-poll"
    platform.controlPlane.agentGateway -> platform.agent "Offers the probe on the long-poll"
    platform.agent -> kubernetes "Launches the probe unit"
    platform.probeUnit -> platform.agent "Fetches its specification"
    platform.probeUnit -> dataSources "Asks for each source's current version or position, without reading data"
    platform.probeUnit -> platform.agent "Returns the probed positions"
    platform.agent -> platform.controlPlane.agentGateway "Reports them"
    platform.controlPlane.agentGateway -> platform.controlPlane.dispatcher "Passes them on"
    platform.controlPlane.dispatcher -> platform.controlPlane.probeScheduling "Returns the positions; the last probed position is kept"
    platform.controlPlane.probeScheduling -> platform.controlPlane.runDriver "Wakes the waiting run"
    platform.controlPlane.runDriver -> platform.controlPlane.catalog "Resolves the internal inputs, and records both together"
    autoLayout lr
}
