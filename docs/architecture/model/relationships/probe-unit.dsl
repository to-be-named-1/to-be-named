// Relationships from probe unit.

platform.probeUnit -> platform.agent "Fetches its specification and returns probed positions through" "ConnectRPC, local endpoint" {
    properties {
        "decisions" "D40, D49"
    }
}

platform.probeUnit -> dataSources "Asks for the current version or position of" "" {
    properties {
        "decisions" "D49"
    }
}
