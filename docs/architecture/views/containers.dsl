// Three container views: one view of every container with every person and external system is unreadable.

container platform "containers" "The platform's containers by plane and the relationships between them; people and external systems are in the context view." {
    include "element.parent==platform"
    autoLayout lr
}

container platform "containers-interface-and-control" "The interface and control planes, with the people and external systems they work with." {
    include platform.webApp platform.cli platform.controlPlane platform.database
    include "element.type==Person"
    include gitHost identityProvider ciSystem
    exclude dataConsumer infrastructureOperator vendorOperator
    autoLayout lr
}

container platform "containers-execution" "How work reaches the data plane and runs: the agent, the units it launches, the backends it drives, the services it uses on their behalf, and where telemetry and alerts go." {
    include platform.controlPlane platform.agent platform.secretStore platform.unitRuntime platform.sessionUnit platform.commandUnit platform.projectionUnit platform.publicationUnit platform.probeUnit platform.sampleBuilder platform.observability
    include dockerEngine kubernetes hpcScheduler cloudBatch secretManager credentialIssuer customerObservability notificationChannels
    autoLayout lr
}

container platform "containers-data-access" "What units read and write: storage, external sources, warehouses, side-effect targets and the Iceberg catalog." {
    include platform.unitRuntime platform.sessionUnit platform.commandUnit platform.projectionUnit platform.publicationUnit platform.probeUnit platform.sampleBuilder platform.bundledObjectStorage
    include objectStorage icebergCatalog lakehouseCatalog dataSources sideEffectTargets warehouses
    autoLayout lr
}
