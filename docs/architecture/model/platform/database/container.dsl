database = container "Control-plane database" "The control plane's only stateful dependency: definitions, drafts, runs, catalog, cache index and provenance, with one schema per bounded context." "PostgreSQL 17+" "Database" {
    properties {
        "decisions" "D30, D42, D45, D47"
    }
}
