// Hybrid: the vendor hosts the interface and control planes, and the data plane and storage stay in the customer's
// cloud account (D22). The vendor side is commercial (D53); the agent is open. A hosted control plane scales by cells,
// each with its own database and set of tenants (D47). Deployment groups work as in the Kubernetes environment.

hybrid = deploymentEnvironment "Hybrid" {
    data = deploymentGroup "data"
    dataplane = deploymentGroup "dataplane"
    uploads = deploymentGroup "uploads"

    userComputer = deploymentNode "User's computer" {
        browser = deploymentNode "Web browser" {
            webApp = containerInstance platform.webApp uploads
        }
        cli = containerInstance platform.cli uploads
    }

    vendor = deploymentNode "Vendor cloud" "Operated by the vendor." "" "Commercial" {
        cell = deploymentNode "Cell" "A control plane with its own database, serving a set of tenants." "" "" "1..N" {
            apiBalancer = infrastructureNode "API load balancer" "Routes to the processes with the api role."
            agentBalancer = infrastructureNode "Agent load balancer" "Routes to the process holding the leader role."
            apiProcesses = deploymentNode "api processes" "" "" "" "2..N" {
                server = containerInstance platform.controlPlane data
            }
            workerProcesses = deploymentNode "worker processes" "" "" "" "1..N" {
                server = containerInstance platform.controlPlane data
            }
            candidateProcesses = deploymentNode "candidate processes" "" "" "" "2..N" {
                server = containerInstance platform.controlPlane data
            }
            postgres = deploymentNode "PostgreSQL" {
                database = containerInstance platform.database data
            }
        }
        observability = deploymentNode "Observability service" {
            observability = containerInstance platform.observability dataplane
        }
    }

    customer = deploymentNode "Customer cloud account" "Operated by the customer; no inbound connection is needed." {
        cluster = deploymentNode "Kubernetes cluster" "" "Kubernetes" {
            agentPods = deploymentNode "agent pods" "One agent pool; each pool runs several replicas of its own." "Pod" "" "2..N" {
                agent = containerInstance platform.agent dataplane
            }
            unitPods = deploymentNode "unit pods" "Launched by the agent, one per attempt, probe or session." "Pod" "" "0..N" {
                unitRuntime = containerInstance platform.unitRuntime dataplane
                probeUnit = containerInstance platform.probeUnit dataplane
                projectionUnit = containerInstance platform.projectionUnit dataplane
                sampleBuilder = containerInstance platform.sampleBuilder dataplane
                sessionUnit = containerInstance platform.sessionUnit dataplane
                commandUnit = containerInstance platform.commandUnit dataplane
            }
        }
        services = deploymentNode "Customer cloud services" {
            objectStorage = softwareSystemInstance objectStorage dataplane,uploads
            secretManager = softwareSystemInstance secretManager dataplane
            credentialIssuer = softwareSystemInstance credentialIssuer dataplane
            customerObservability = softwareSystemInstance customerObservability dataplane
        }
    }

    hybrid.userComputer.browser.webApp -> hybrid.vendor.cell.apiBalancer "Calls the API through" "HTTPS"
    hybrid.userComputer.cli -> hybrid.vendor.cell.apiBalancer "Calls the API through" "HTTPS"
    hybrid.vendor.cell.apiBalancer -> hybrid.vendor.cell.apiProcesses.server "Routes to"
    hybrid.customer.cluster.agentPods.agent -> hybrid.vendor.cell.agentBalancer "Pulls work through, over outbound connections" "ConnectRPC over HTTPS"
    hybrid.vendor.cell.agentBalancer -> hybrid.vendor.cell.candidateProcesses.server "Routes to the process holding the leader role"
}
