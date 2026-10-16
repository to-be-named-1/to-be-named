// Single machine: the complete platform on one host, as containers on a Docker engine (CORE 2.17, D29).
// One control-plane process runs every role; there is one instance of each element, so no deployment groups are needed.

singleMachine = deploymentEnvironment "Single machine" {
    userComputer = deploymentNode "User's computer" {
        browser = deploymentNode "Web browser" {
            webApp = containerInstance platform.webApp
        }
        cli = containerInstance platform.cli
    }

    host = deploymentNode "Host" "The one machine the platform is installed on." "Docker engine" {
        controlPlane = deploymentNode "Control-plane process" "Runs every role (all)." "Docker container" {
            server = containerInstance platform.controlPlane
        }
        postgres = deploymentNode "PostgreSQL" "" "Docker container" {
            database = containerInstance platform.database
        }
        storage = deploymentNode "Bundled object storage" "" "Docker container" {
            bundledObjectStorage = containerInstance platform.bundledObjectStorage
        }
        agent = deploymentNode "Execution agent" "" "Docker container" {
            agent = containerInstance platform.agent
        }
        secrets = deploymentNode "Built-in secret store" "" "Docker container" {
            secretStore = containerInstance platform.secretStore
        }
        observability = deploymentNode "Observability service" "" "Docker container" {
            observability = containerInstance platform.observability
        }
        units = deploymentNode "Unit containers" "Launched by the agent, one per attempt, probe or session." "Docker container" "" "0..N" {
            unitRuntime = containerInstance platform.unitRuntime
            probeUnit = containerInstance platform.probeUnit
            projectionUnit = containerInstance platform.projectionUnit
            publicationUnit = containerInstance platform.publicationUnit
            sampleBuilder = containerInstance platform.sampleBuilder
            sessionUnit = containerInstance platform.sessionUnit
            commandUnit = containerInstance platform.commandUnit
        }
    }
}
