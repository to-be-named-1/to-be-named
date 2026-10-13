agent = container "Execution agent" "Pulls work from the control plane, launches units on its backend, mints storage credentials, resolves secrets and is the single egress of the data plane." "Go, static binary" {
    properties {
        "decisions" "D21, D22, D29, D30, D40, D43, D44, D48, D52"
    }
}
