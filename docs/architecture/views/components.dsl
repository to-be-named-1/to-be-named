// Component views. A component view holds only its own container's components; other containers appear whole.
// The database is left out of the control plane's views: its documentation lists which components reach each schema.

component platform.controlPlane "components-control-plane-execution" "How a run gets from its trigger to the commit of its outputs: the components of orchestration, planning, the catalog and dispatch, and the agents they serve." {
    include platform.controlPlane.reconciler platform.controlPlane.runDriver platform.controlPlane.planner platform.controlPlane.authorization
    include platform.controlPlane.cacheIndex platform.controlPlane.catalog platform.controlPlane.probeScheduling platform.controlPlane.tableScheduling platform.controlPlane.collectionMarking
    include platform.controlPlane.scheduler platform.controlPlane.dispatcher platform.controlPlane.agentGateway platform.controlPlane.outbox platform.controlPlane.leadership
    include platform.agent
    autoLayout lr
}

component platform.controlPlane "components-control-plane-requests" "How people and automation reach the platform: the API layer and the components that serve its calls, with the clients, the identity provider and the git host." {
    include platform.controlPlane.apiLayer platform.controlPlane.identity platform.controlPlane.authorization platform.controlPlane.audit
    include platform.controlPlane.definitions platform.controlPlane.compiler platform.controlPlane.gitSync platform.controlPlane.deployment platform.controlPlane.registry
    include platform.controlPlane.catalog platform.controlPlane.adoption platform.controlPlane.provenance platform.controlPlane.runDriver
    include platform.webApp platform.cli ciSystem identityProvider gitHost
    autoLayout lr
}

component platform.database "components-database" "The database's schemas: one per bounded context, grouped like the components that own them, and one shared by no context; no context reaches another's schema (D47)." {
    include *
    autoLayout lr
}
