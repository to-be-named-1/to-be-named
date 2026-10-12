// Relationships from sample builder.

platform.sampleBuilder -> platform.agent "Fetches its specification and reports through" "ConnectRPC, local endpoint" {
    properties {
        "decisions" "D40, D50"
    }
}

platform.sampleBuilder -> objectStorage "Reads inputs from and writes samples to" "S3 API" {
    properties {
        "decisions" "D50"
    }
}

platform.sampleBuilder -> platform.bundledObjectStorage "Reads inputs from and writes samples to" "S3 API" {
    properties {
        "decisions" "D50"
    }
}

platform.sampleBuilder -> dataSources "Reads external sources at their probed version from" "" {
    properties {
        "decisions" "D49, D50"
    }
}
