controlPlane = container "Control-plane server" "Compiles, plans, schedules and dispatches work, makes results current and holds the catalog; one binary deployed in roles, with a single active leader." "Go, ConnectRPC, cel-go" {
    properties {
        "decisions" "D21, D29, D30, D40, D43, D44, D45, D47, D48, D49, D51, D52"
    }

    // Groups are the bounded contexts of D47. The roles property names the roles that the component's
    // actions require; a replica with any one of them performs that role's actions. Which action needs
    // which role is set out in the container documentation.

    group "Identity and tenancy" {
        identity = component "Identity and membership" "Manages tenants, principals, memberships and clearance, service accounts, projects, and tenant resources with their grants." {
            properties {
                "roles" "api"
            }
        }
        authorization = component "Authorization layer" "Authorizes every API method and every run against roles, project scope and clearance; the policy behind it is an extension point." "" "Extension point" {
            properties {
                "roles" "api, worker"
            }
        }
        audit = component "Audit" "Records the audit trail of user and administrative actions; export to external sinks is an extension point." "" "Extension point" {
            properties {
                "roles" "api, worker"
            }
        }
    }

    group "Authoring" {
        definitions = component "Definitions and drafts" "Manages workflow and dataset definitions, drafts, platform-held versions and environment bindings." {
            properties {
                "roles" "api, worker"
            }
        }
        compiler = component "Compiler" "Parses, migrates and type-checks each definition version, flattens composites, checks control flow, intervals and single producers, and computes semantic fingerprints." "Go, goccy/go-yaml, cel-go" {
            properties {
                "roles" "api, worker"
            }
        }
        gitSync = component "Git synchronization" "Pushes authors' commits to the git host and watches the deploy branch." {
            properties {
                "roles" "api, worker"
            }
        }
        deployment = component "Deployment" "Deploys committed definitions as an act of the platform, checking governed fields." {
            properties {
                "roles" "api, worker"
            }
        }
    }

    group "Plugin registry" {
        registry = component "Plugin registry" "Manages format types and their implementations, node types, the implementations each project allows, and images." {
            properties {
                "roles" "api, worker"
            }
        }
    }

    group "Catalog" {
        catalog = component "Dataset catalog" "Manages datasets and their versions: answers queries, resolves the versions a run reads, enforces the single producer and the order of versions, and makes outputs current in the commit transaction." {
            properties {
                "roles" "api, worker, leader"
            }
        }
        cacheIndex = component "Cache index" "Finds reusable outputs by input-addressed key, through the eligibility filter." {
            properties {
                "roles" "worker, leader"
            }
        }
        projectionScheduling = component "Projection scheduling" "Schedules the projection of committed versions as Iceberg snapshots for external engines." {
            properties {
                "roles" "worker"
            }
        }
        collectionMarking = component "Collection marking" "Marks what retained, cached, pinned or protected manifests reference, so that agents can delete the rest." {
            properties {
                "roles" "worker"
            }
        }
        probeScheduling = component "Probe scheduling" "Batches source probes per pool and keeps each external source's last probed position." {
            properties {
                "roles" "worker, leader"
            }
        }
        adoption = component "Adoption" "Brings existing tables and files under the platform: path-pattern mappings, baselines and switchover." {
            properties {
                "roles" "api, worker"
            }
        }
    }

    group "Planning" {
        planner = component "Planner" "Turns a run's resolved inputs into a plan: bindings, placement, estimates, repartitioning, fusion into units, sizing, pools and expected reuse." {
            properties {
                "roles" "worker"
            }
        }
    }

    group "Orchestration" {
        runDriver = component "Run driver" "Resolves a run's inputs, creates task runs as the run reaches them, decides retries, suspends and resumes, and ends the run." {
            properties {
                "roles" "api, worker, leader"
            }
        }
        reconciler = component "Reconciler" "Runs the level-triggered loops for schedules and triggers, runs waiting for inputs, materialization requests, backfills and backstop sweeps." {
            properties {
                "roles" "worker"
            }
        }
    }

    group "Dispatch" {
        scheduler = component "Scheduler" "Orders and admits ready work per capacity domain: fair share, quotas, write leases and preemption." "" "Leader only" {
            properties {
                "roles" "leader"
            }
        }
        dispatcher = component "Dispatcher" "Creates attempts and their unit specifications, offers work, holds lease renewals in memory, signals cancellation, and checks fencing tokens and write leases on commit requests." "" "Leader only" {
            properties {
                "roles" "leader"
            }
        }
        agentGateway = component "Agent gateway" "Receives agents' calls and long-polls, checks their message signatures against the keys enrolled with the dispatcher, and signs responses." "ConnectRPC, HTTP Message Signatures" "Leader only" {
            properties {
                "roles" "leader"
            }
        }
    }

    group "Provenance" {
        provenance = component "Provenance read model" "Serves lineage, reproducibility tiers, verification and comparator verdicts, read from the catalog and orchestration." {
            properties {
                "roles" "api, worker"
            }
        }
    }

    // Components that belong to no bounded context.

    apiLayer = component "API layer" "Serves the ConnectRPC API to the web application, the CLI and CI, and serves the single-page application; authentication is an extension point." "ConnectRPC" "Extension point" {
        properties {
            "roles" "api"
        }
    }
    outbox = component "Outbox and work-row delivery" "Delivers outbox rows to their handlers and runs work rows, with claims, retries and dead letters." {
        properties {
            "roles" "worker, leader"
        }
    }
    leadership = component "Leadership" "Elects the leader with a session-level advisory lock and fences leader-only writes by epoch." {
        properties {
            "roles" "leader"
        }
    }
}
