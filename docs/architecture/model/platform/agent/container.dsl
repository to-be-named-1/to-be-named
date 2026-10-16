agent = container "Execution agent" "Pulls work from the control plane, launches units on its backend, mints storage credentials, resolves secrets and is the single egress of the data plane." "Go, static binary" {
    properties {
        "decisions" "D11, D12, D21, D22, D26, D28, D29, D30, D40, D43, D44, D48, D49, D52"
    }
}
