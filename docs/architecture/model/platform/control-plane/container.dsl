controlPlane = container "Control-plane server" "Compiles, plans, schedules and dispatches work, makes results current and holds the catalog; one binary deployed in roles, with a single active leader." "Go, ConnectRPC, cel-go" {
    properties {
        "decisions" "D21, D29, D30, D40, D43, D44, D45, D47, D48, D49, D51, D52"
    }
}
