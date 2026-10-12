// Relationships from command unit.

platform.commandUnit -> platform.agent "Fetches its specification, sends events and requests its commit through" "ConnectRPC, local endpoint" {
    properties {
        "decisions" "D40"
    }
}

platform.commandUnit -> objectStorage "Reads inputs from and stages outputs in" "S3 API" {
    properties {
        "decisions" "D32"
    }
}

platform.commandUnit -> platform.bundledObjectStorage "Reads inputs from and stages outputs in" "S3 API" {
    properties {
        "decisions" "D32"
    }
}
