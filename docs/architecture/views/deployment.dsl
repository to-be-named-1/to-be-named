// Deployment views. Each shows where the platform's containers run, how traffic reaches the control plane's roles, and
// only the external systems the environment hosts.

deployment platform singleMachine "deployment-single-machine" "The complete platform on one host: one control-plane process running every role, with Postgres, bundled object storage, the agent and the units it launches as containers." {
    include *
    autoLayout lr
}

deployment platform kubernetesEnvironment "deployment-kubernetes" "A highly available self-hosted installation in one Kubernetes cluster: the control plane in pods by role, Services routing API traffic to api pods and agent traffic to the leader, and the data plane in its own namespace." {
    include *
    autoLayout lr
}

deployment platform hybrid "deployment-hybrid" "The vendor hosts a highly available control plane in cells; agents and units run in the customer's cloud account, pull work over outbound connections, and keep data, credentials and secrets there." {
    include *
    autoLayout lr
}
