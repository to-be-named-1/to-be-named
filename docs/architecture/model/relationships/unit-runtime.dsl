// Relationships from unit runtime.

platform.unitRuntime -> platform.agent "Fetches its specification, refreshes credentials, sends events and requests its commit through" "ConnectRPC, local endpoint" {
    properties {
        "decisions" "D40"
    }
}

platform.unitRuntime -> objectStorage "Reads inputs from and stages outputs in" "S3 API" {
    properties {
        "decisions" "D15, D23"
    }
}

platform.unitRuntime -> platform.bundledObjectStorage "Reads inputs from and stages outputs in" "S3 API" {
    properties {
        "decisions" "D15, D23"
    }
}

platform.unitRuntime -> dataSources "Reads external sources from" "" {
    properties {
        "decisions" "D35, D49"
    }
}

platform.unitRuntime -> warehouses "Pushes relational work down to, and extracts reduced data from" "SQL" {
    properties {
        "decisions" "D25, D28"
    }
}

platform.unitRuntime -> sideEffectTargets "Writes to, sends to or triggers" "" {
    properties {
        "decisions" "D40"
    }
}
