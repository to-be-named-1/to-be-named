// Kubernetes: a self-hosted installation in one cluster, with the control plane deployed in roles (D47).
// Relationships are replicated only within a deployment group: every role reaches the database (data), the data plane
// reaches its own services (dataplane), and clients upload directly to storage (uploads). Clients and agents reach the
// control plane only through the Services that route to roles, drawn explicitly below.

kubernetesEnvironment = deploymentEnvironment "Kubernetes" {
    data = deploymentGroup "data"
    dataplane = deploymentGroup "dataplane"
    uploads = deploymentGroup "uploads"

    userComputer = deploymentNode "User's computer" {
        browser = deploymentNode "Web browser" {
            webApp = containerInstance platform.webApp uploads
        }
        cli = containerInstance platform.cli uploads
    }

    cluster = deploymentNode "Kubernetes cluster" "" "Kubernetes" {
        apiService = infrastructureNode "API Service" "Selects the pods whose template carries the api role." "Kubernetes Service"
        agentService = infrastructureNode "Agent Service" "Selects the candidate pod labeled with the leader role." "Kubernetes Service"

        controlPlane = deploymentNode "Control-plane namespace" "" "Kubernetes namespace" {
            apiPods = deploymentNode "api pods" "Serve the API and the single-page application." "Pod" "" "2..N" {
                server = containerInstance platform.controlPlane data
            }
            workerPods = deploymentNode "worker pods" "Plan runs, run the reconciler's loops and deliver events." "Pod" "" "1..N" {
                server = containerInstance platform.controlPlane data
            }
            candidatePods = deploymentNode "candidate pods" "Compete for leadership; the leader runs the agent gateway, the scheduler and the dispatcher." "Pod" "" "2..N" {
                server = containerInstance platform.controlPlane data
            }
        }

        dataPlane = deploymentNode "Data-plane namespace" "" "Kubernetes namespace" {
            agentPods = deploymentNode "agent pods" "One agent pool; each pool runs several replicas of its own." "Pod" "" "2..N" {
                agent = containerInstance platform.agent dataplane
            }
            secretPods = deploymentNode "Built-in secret store" "Where the installation has no secret manager of its own." "Pod" {
                secretStore = containerInstance platform.secretStore dataplane
            }
            unitPods = deploymentNode "unit pods" "Launched by the agent, one per attempt, probe or session." "Pod" "" "0..N" {
                unitRuntime = containerInstance platform.unitRuntime dataplane
                probeUnit = containerInstance platform.probeUnit dataplane
                projectionUnit = containerInstance platform.projectionUnit dataplane
                publicationUnit = containerInstance platform.publicationUnit dataplane
                sampleBuilder = containerInstance platform.sampleBuilder dataplane
                sessionUnit = containerInstance platform.sessionUnit dataplane
                commandUnit = containerInstance platform.commandUnit dataplane
            }
        }

        observability = deploymentNode "Observability namespace" "" "Kubernetes namespace" {
            observability = containerInstance platform.observability dataplane
        }
    }

    postgres = deploymentNode "PostgreSQL" "In the cluster or a managed service." {
        database = containerInstance platform.database data
    }

    storage = deploymentNode "Customer storage" {
        objectStorage = softwareSystemInstance objectStorage dataplane,uploads
        lakehouseCatalog = softwareSystemInstance lakehouseCatalog dataplane
    }

    kubernetesEnvironment.userComputer.browser.webApp -> kubernetesEnvironment.cluster.apiService "Calls the API through" "HTTPS"
    kubernetesEnvironment.userComputer.cli -> kubernetesEnvironment.cluster.apiService "Calls the API through" "HTTPS"
    kubernetesEnvironment.cluster.apiService -> kubernetesEnvironment.cluster.controlPlane.apiPods.server "Routes to"
    kubernetesEnvironment.cluster.dataPlane.agentPods.agent -> kubernetesEnvironment.cluster.agentService "Pulls work through" "ConnectRPC over HTTPS"
    kubernetesEnvironment.cluster.agentService -> kubernetesEnvironment.cluster.controlPlane.candidatePods.server "Routes to the pod holding the leader role"
}
