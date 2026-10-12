controlPlane = container "Control-plane server" "Compiles, plans, schedules and dispatches work, makes results current and holds the catalogue; one binary deployed in roles, with a single active leader." "Go, ConnectRPC, cel-go" {
    properties {
        "decisions" "D21, D44, D47, D48"
    }
}
