// Relationships from projection unit.

platform.projectionUnit -> platform.agent "Fetches its specification and reports through" "ConnectRPC, local endpoint" {
    properties {
        "decisions" "D40, D44"
    }
}

platform.projectionUnit -> objectStorage "Writes Iceberg metadata to" "S3 API" {
    properties {
        "decisions" "D42, D44"
    }
}

platform.projectionUnit -> platform.bundledObjectStorage "Writes Iceberg metadata to" "S3 API" {
    properties {
        "decisions" "D42, D44"
    }
}

platform.projectionUnit -> icebergCatalogue "Registers Iceberg snapshots in" "REST or SQL catalogue" {
    properties {
        "decisions" "D44"
    }
}
