// Relationships from control-plane components.

platform.controlPlane.gitSync -> gitHost "Pushes authors' commits to, and watches the deploy branch of" "HTTPS" {
    properties {
        "decisions" "D45"
    }
}

platform.controlPlane.apiLayer -> identityProvider "Authenticates people through" "OpenID Connect" {
    properties {
        "decisions" "D45"
    }
}

// Each component reaches only its own context's schema (D47), in tenant-scoped transactions (D45).

platform.controlPlane.identity -> platform.database.identity "Reads and writes its tables in" "SQL over pgx" {
    properties {
        "decisions" "D45, D47"
    }
}

platform.controlPlane.authorization -> platform.database.identity "Reads roles, memberships and clearance from" "SQL over pgx" {
    properties {
        "decisions" "D45, D47"
    }
}

platform.controlPlane.audit -> platform.database.identity "Writes the audit trail to" "SQL over pgx" {
    properties {
        "decisions" "D45, D47"
    }
}

platform.controlPlane.definitions -> platform.database.authoring "Reads and writes its tables in" "SQL over pgx" {
    properties {
        "decisions" "D45, D47"
    }
}

platform.controlPlane.compiler -> platform.database.authoring "Stores compiled workflows by semantic hash in" "SQL over pgx" {
    properties {
        "decisions" "D47"
    }
}

platform.controlPlane.gitSync -> platform.database.authoring "Reads and writes its tables in" "SQL over pgx" {
    properties {
        "decisions" "D45, D47"
    }
}

platform.controlPlane.deployment -> platform.database.authoring "Records deployments in" "SQL over pgx" {
    properties {
        "decisions" "D45, D47"
    }
}

platform.controlPlane.registry -> platform.database.registry "Reads and writes its tables in" "SQL over pgx" {
    properties {
        "decisions" "D47"
    }
}

platform.controlPlane.catalog -> platform.database.catalog "Reads and writes its tables in" "SQL over pgx" {
    properties {
        "decisions" "D42, D47"
    }
}

platform.controlPlane.cacheIndex -> platform.database.catalog "Reads and writes cache-index entries in" "SQL over pgx" {
    properties {
        "decisions" "D47"
    }
}

platform.controlPlane.projectionScheduling -> platform.database.catalog "Reads and writes projection state in" "SQL over pgx" {
    properties {
        "decisions" "D42, D44"
    }
}

platform.controlPlane.collectionMarking -> platform.database.catalog "Reads manifests and writes collection marks in" "SQL over pgx" {
    properties {
        "decisions" "D42"
    }
}

platform.controlPlane.probeScheduling -> platform.database.catalog "Reads and writes probed positions in" "SQL over pgx" {
    properties {
        "decisions" "D49"
    }
}

platform.controlPlane.adoption -> platform.database.catalog "Records mappings and baselines in" "SQL over pgx" {
    properties {
        "decisions" "D51"
    }
}

platform.controlPlane.runDriver -> platform.database.orchestration "Reads and writes runs, task runs and attempts in" "SQL over pgx" {
    properties {
        "decisions" "D47, D48"
    }
}

platform.controlPlane.reconciler -> platform.database.orchestration "Claims work rows from" "SQL over pgx" {
    properties {
        "decisions" "D47"
    }
}

platform.controlPlane.scheduler -> platform.database.dispatch "Reads and writes queues and write leases in" "SQL over pgx" {
    properties {
        "decisions" "D43, D48"
    }
}

platform.controlPlane.dispatcher -> platform.database.dispatch "Reads and writes agents and their keys in" "SQL over pgx" {
    properties {
        "decisions" "D40, D47"
    }
}

platform.controlPlane.provenance -> platform.database.provenance "Reads and writes its tables in" "SQL over pgx" {
    properties {
        "decisions" "D47"
    }
}

platform.controlPlane.outbox -> platform.database.shared "Claims outbox rows from" "SQL over pgx" {
    properties {
        "decisions" "D48"
    }
}

platform.controlPlane.leadership -> platform.database.shared "Holds the leader lock and increments the epoch in" "SQL over pgx, dedicated session" {
    properties {
        "decisions" "D47"
    }
}

// Between control-plane components: the collaborations the dynamic views show.

platform.controlPlane.reconciler -> platform.controlPlane.runDriver "Creates runs and wakes waiting runs through" {
    properties {
        "decisions" "D47"
    }
}

platform.controlPlane.runDriver -> platform.controlPlane.probeScheduling "Requests source probes from" {
    properties {
        "decisions" "D49"
    }
}

platform.controlPlane.probeScheduling -> platform.controlPlane.runDriver "Wakes runs waiting for probes in" {
    properties {
        "decisions" "D49"
    }
}

platform.controlPlane.probeScheduling -> platform.controlPlane.dispatcher "Hands batched probes to be offered to" {
    properties {
        "decisions" "D49"
    }
}

platform.controlPlane.dispatcher -> platform.controlPlane.probeScheduling "Returns probed positions to" {
    properties {
        "decisions" "D49"
    }
}

platform.controlPlane.runDriver -> platform.controlPlane.catalog "Resolves input versions and records read positions through" {
    properties {
        "decisions" "D14, D42, D47"
    }
}

platform.controlPlane.runDriver -> platform.controlPlane.planner "Plans runs with" {
    properties {
        "decisions" "D47"
    }
}

platform.controlPlane.planner -> platform.controlPlane.authorization "Checks a run's access under its project identity with" {
    properties {
        "decisions" "D45, D47"
    }
}

platform.controlPlane.planner -> platform.controlPlane.cacheIndex "Computes expected reuse with" {
    properties {
        "decisions" "D8, D47"
    }
}

platform.controlPlane.runDriver -> platform.controlPlane.cacheIndex "Makes the authoritative cache lookup in" {
    properties {
        "decisions" "D8, D47"
    }
}

platform.controlPlane.runDriver -> platform.controlPlane.scheduler "Hands ready task runs to" {
    properties {
        "decisions" "D43, D47"
    }
}

platform.controlPlane.scheduler -> platform.controlPlane.dispatcher "Hands admitted work to" {
    properties {
        "decisions" "D43, D47"
    }
}

platform.controlPlane.dispatcher -> platform.controlPlane.agentGateway "Hands offers and control signals to waiting long-polls in" {
    properties {
        "decisions" "D40, D48"
    }
}

platform.controlPlane.agentGateway -> platform.controlPlane.dispatcher "Passes agents' claims, renewals, reports and commit requests to" {
    properties {
        "decisions" "D40, D48"
    }
}

platform.controlPlane.dispatcher -> platform.controlPlane.runDriver "Creates attempts, checks fencing tokens and reports attempt outcomes through" {
    properties {
        "decisions" "D31, D47"
    }
}

platform.controlPlane.dispatcher -> platform.controlPlane.catalog "Commits staged outputs through" {
    properties {
        "decisions" "D15, D48"
    }
}

platform.controlPlane.catalog -> platform.database.shared "Writes outbox rows to" "SQL over pgx" {
    properties {
        "decisions" "D48"
    }
}

platform.controlPlane.runDriver -> platform.database.shared "Writes outbox rows to" "SQL over pgx" {
    properties {
        "decisions" "D48"
    }
}

platform.controlPlane.outbox -> platform.controlPlane.projectionScheduling "Delivers commit events to" {
    properties {
        "decisions" "D42, D48"
    }
}

platform.controlPlane.outbox -> platform.controlPlane.reconciler "Wakes the loops of" {
    properties {
        "decisions" "D47, D48"
    }
}

platform.controlPlane.outbox -> platform.controlPlane.scheduler "Delivers events that make work ready, and quota and weight changes, to" {
    properties {
        "decisions" "D43, D48"
    }
}

platform.controlPlane.outbox -> platform.controlPlane.dispatcher "Delivers cancel and pause commands for running attempts to" {
    properties {
        "decisions" "D47, D48"
    }
}

platform.controlPlane.leadership -> platform.controlPlane.scheduler "Starts and stops the leader loops of" {
    properties {
        "decisions" "D47"
    }
}

platform.controlPlane.leadership -> platform.controlPlane.dispatcher "Starts and stops the leader loops of" {
    properties {
        "decisions" "D47"
    }
}

platform.controlPlane.leadership -> platform.controlPlane.runDriver "Starts and stops the leader loops of" {
    properties {
        "decisions" "D47"
    }
}

platform.controlPlane.leadership -> platform.controlPlane.agentGateway "Starts and stops the leader loops of" {
    properties {
        "decisions" "D47"
    }
}

// From the API layer to the components that serve its calls, and within authoring.

platform.controlPlane.apiLayer -> platform.controlPlane.identity "Routes tenant, membership and project calls to" {
    properties {
        "decisions" "D45, D47"
    }
}

platform.controlPlane.apiLayer -> platform.controlPlane.authorization "Authorizes every call with" {
    properties {
        "decisions" "D45"
    }
}

platform.controlPlane.apiLayer -> platform.controlPlane.audit "Records user and administrative actions in" {
    properties {
        "decisions" "D45"
    }
}

platform.controlPlane.apiLayer -> platform.controlPlane.definitions "Routes draft, commit and binding calls to" {
    properties {
        "decisions" "D45, D47"
    }
}

platform.controlPlane.apiLayer -> platform.controlPlane.gitSync "Routes pushes of authors' commits to" {
    properties {
        "decisions" "D45"
    }
}

platform.controlPlane.apiLayer -> platform.controlPlane.deployment "Routes deployment and approval calls to" {
    properties {
        "decisions" "D45"
    }
}

platform.controlPlane.apiLayer -> platform.controlPlane.registry "Routes plugin registry calls to" {
    properties {
        "decisions" "D47"
    }
}

platform.controlPlane.apiLayer -> platform.controlPlane.catalog "Routes dataset queries and owner acts to" {
    properties {
        "decisions" "D45, D47"
    }
}

platform.controlPlane.apiLayer -> platform.controlPlane.adoption "Routes adoption calls to" {
    properties {
        "decisions" "D51"
    }
}

platform.controlPlane.apiLayer -> platform.controlPlane.provenance "Routes lineage and verification queries to" {
    properties {
        "decisions" "D47"
    }
}

platform.controlPlane.apiLayer -> platform.controlPlane.runDriver "Routes commands on runs to" {
    properties {
        "decisions" "D47"
    }
}

platform.controlPlane.definitions -> platform.controlPlane.compiler "Compiles each version with" {
    properties {
        "decisions" "D47"
    }
}
