// Relationships from session unit.

platform.sessionUnit -> platform.agent "Receives unit specifications, refreshes credentials and sends events through" "ConnectRPC, local endpoint" {
    properties {
        "decisions" "D40, D50"
    }
}

platform.sessionUnit -> objectStorage "Reads samples from and writes run-scoped artifacts to" "S3 API" {
    properties {
        "decisions" "D50"
    }
}

platform.sessionUnit -> platform.bundledObjectStorage "Reads samples from and writes run-scoped artifacts to" "S3 API" {
    properties {
        "decisions" "D50"
    }
}
