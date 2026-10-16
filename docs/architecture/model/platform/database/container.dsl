database = container "Control-plane database" "The control plane's only stateful dependency: definitions, drafts, runs, catalog, cache index and provenance, with one schema per bounded context." "PostgreSQL 17+" "Database" {
    !docs docs

    properties {
        "decisions" "D5, D12, D30, D42, D44, D45, D47, D48"
    }

    // One schema per bounded context (D47), grouped like the control-plane components that own them;
    // planning owns no tables. A context never reads another context's schema.

    group "Identity and tenancy" {
        identity = component "Identity and tenancy schema" "Tenants, principals, memberships, clearance, service accounts, projects, resources and grants, and the audit trail." "Postgres schema" "Database"
    }
    group "Authoring" {
        authoring = component "Authoring schema" "Definitions, drafts, platform-held versions, compiled workflows, deployments and environment bindings." "Postgres schema" "Database"
    }
    group "Plugin registry" {
        registry = component "Plugin registry schema" "Format types, implementations, node types, allowed implementations and images." "Postgres schema" "Database"
    }
    group "Catalog" {
        catalog = component "Catalog schema" "Datasets, versions, partition versions, manifests, positions, frontiers, read records, the cache index, projection state and collection marks." "Postgres schema" "Database"
    }
    group "Orchestration" {
        orchestration = component "Orchestration schema" "Triggers, materialization requests, backfills, runs and their plans, task runs, attempts, map groups and work rows." "Postgres schema" "Database"
    }
    group "Dispatch" {
        dispatch = component "Dispatch schema" "Agent pools, capacity domains, agents and their keys, queues and write leases." "Postgres schema" "Database"
    }
    group "Provenance" {
        provenance = component "Provenance schema" "Lineage, reproducibility tiers, verification claims and comparator verdicts." "Postgres schema" "Database"
    }

    shared = component "Shared schema" "Tables owned by no context: the outbox and the leader epoch." "Postgres schema" "Database"
}
