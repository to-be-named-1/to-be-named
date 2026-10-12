agent = container "Execution agent" "Pulls work from the control plane, launches units on its backend, mints storage credentials, resolves secrets and is the single egress of the data plane." "Go, static binary" {
    properties {
        "decisions" "D29, D40, D44, D48"
    }
}
