workspace "Platform architecture" "C4 model, documentation and decision records of the workflow orchestration platform." {

    !identifiers hierarchical
    !docs documentation/workspace

    configuration {
        scope softwaresystem
    }

    model {
        // Include order is fixed, because the DSL has no forward references:
        // people, external systems, the platform and its containers, relationships, deployment, overlays.

        !include model/people.dsl
        !include model/external-systems.dsl

        platform = softwareSystem "Platform" "Assembles, schedules, executes and monitors multi-stage data and computation pipelines, and states what each run can be trusted to reproduce." {
            !docs documentation/platform
            !adrs decisions

            properties {
                "decisions" "D21, D22, D53"
            }

            // One folder per container: model/platform/<container>/container.dsl, with its docs/ beside it.
            // The groups are the planes of D21.
            group "Interface plane" {
                !include model/platform/web-app/container.dsl
                !include model/platform/cli/container.dsl
            }
            group "Control plane" {
                !include model/platform/control-plane/container.dsl
                !include model/platform/database/container.dsl
            }
            group "Data plane" {
                !include model/platform/agent/container.dsl
                !include model/platform/secret-store/container.dsl
                !include model/platform/unit-runtime/container.dsl
                !include model/platform/session-unit/container.dsl
                !include model/platform/command-unit/container.dsl
                !include model/platform/projection-unit/container.dsl
                !include model/platform/probe-unit/container.dsl
                !include model/platform/sample-builder/container.dsl
                !include model/platform/bundled-object-storage/container.dsl
            }
            group "Observability plane" {
                !include model/platform/observability/container.dsl
            }
        }

        !include model/relationships/people.dsl
        !include model/relationships/web-app.dsl
        !include model/relationships/cli.dsl
        !include model/relationships/control-plane.dsl
        !include model/relationships/agent.dsl
        !include model/relationships/unit-runtime.dsl
        !include model/relationships/session-unit.dsl
        !include model/relationships/command-unit.dsl
        !include model/relationships/projection-unit.dsl
        !include model/relationships/probe-unit.dsl
        !include model/relationships/sample-builder.dsl
        !include model/relationships/observability.dsl
        !include model/relationships/external-systems.dsl

        !include model/overlays/lifecycle.dsl
    }

    views {
        !include views/context.dsl
        !include views/containers.dsl
        !include views/components.dsl
        !include views/dynamic/run-start.dsl
        !include views/dynamic/task-execution.dsl
        !include views/dynamic/data-commit.dsl
        !include views/dynamic/lease-fencing.dsl
        !include views/dynamic/leader-failover.dsl
        !include views/dynamic/source-probe.dsl

        !include views/styles.dsl
        !include views/overlays/lifecycle.dsl
    }

}
