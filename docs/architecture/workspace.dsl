workspace "Platform architecture" "C4 model, documentation and decision records of the workflow orchestration platform." {

    !identifiers hierarchical
    !docs documentation/workspace

    configuration {
        scope softwaresystem
    }

    model {
        // Include order is fixed, because the DSL has no forward references:
        // people, external systems, the platform and its containers, relationships, deployment, overlays.

        platform = softwareSystem "Platform" "Assembles, schedules, executes and monitors multi-stage data and computation pipelines, and states what each run can be trusted to reproduce." {
            !adrs decisions

            // One folder per container: model/platform/<container>/container.dsl, with its docs/ beside it.
        }

        !include model/overlays/lifecycle.dsl
    }

    views {
        !include views/styles.dsl
        !include views/overlays/lifecycle.dsl
    }

}
