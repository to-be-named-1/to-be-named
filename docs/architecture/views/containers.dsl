// Three container views: one view of every container with every person and external system is unreadable.

container platform "containers" "The platform's containers by plane and the relationships between them; people and external systems are in the context view." {
    include "element.parent==platform"
    autoLayout lr
}

container platform "containers-interface-and-control" "The interface and control planes, with the people and external systems they work with." {
    include platform.webApp platform.cli platform.controlPlane platform.database
    include "element.type==Person"
    include gitHost identityProvider notificationChannels ciSystem
    exclude dataConsumer infrastructureOperator vendorOperator
    autoLayout lr
}

container platform "containers-execution" "How work reaches the data plane and runs: the agent, the units it launches, the backends it drives and the services it uses on their behalf." {
    include platform.controlPlane platform.agent platform.secretStore platform.unitRuntime platform.sessionUnit platform.commandUnit platform.projectionUnit platform.probeUnit platform.sampleBuilder
    include dockerEngine kubernetes hpcScheduler cloudBatch secretManager credentialIssuer observabilitySink
    autoLayout lr
}

container platform "containers-data-access" "What units read and write: storage, external sources, warehouses, side-effect targets and the Iceberg catalogue." {
    include platform.unitRuntime platform.sessionUnit platform.commandUnit platform.projectionUnit platform.probeUnit platform.sampleBuilder platform.bundledObjectStorage
    include objectStorage icebergCatalogue dataSources sideEffectTargets warehouses
    autoLayout lr
}
