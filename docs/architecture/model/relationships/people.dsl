// Relationships from people.

workflowAuthor -> platform.webApp "Builds and tries workflows, and commits drafts, in" "HTTPS" {
    properties {
        "decisions" "D41, D45, D50"
    }
}

workflowAuthor -> gitHost "Reviews and merges workflow changes in" "" {
    properties {
        "decisions" "D41, D45"
    }
}

operator -> platform.webApp "Triggers, backfills, pauses and monitors runs in" "HTTPS" {
    properties {
        "decisions" "D20, D24, D31"
    }
}

projectMaintainer -> platform.webApp "Manages project settings, bindings and deployments in" "HTTPS" {
    properties {
        "decisions" "D41, D45"
    }
}

projectMaintainer -> gitHost "Reviews and merges changes to the deploy branch in" "" {
    properties {
        "decisions" "D45"
    }
}

datasetOwner -> platform.webApp "Governs datasets and releases quarantined versions in" "HTTPS" {
    properties {
        "decisions" "D31, D45"
    }
}

tenantAdmin -> platform.webApp "Administers members, agent pools, connections and quotas in" "HTTPS" {
    properties {
        "decisions" "D45, D47"
    }
}

auditor -> platform.webApp "Reads the audit trail in" "HTTPS" {
    properties {
        "decisions" "D45"
    }
}

dataConsumer -> queryEngines "Queries managed datasets with" "" {
    properties {
        "decisions" "D44"
    }
}

infrastructureOperator -> platform.controlPlane "Installs and upgrades, when self-hosted" "" {
    properties {
        "decisions" "D22, D44"
    }
}

infrastructureOperator -> platform.agent "Installs, enrolls and upgrades" "" {
    properties {
        "decisions" "D40, D44"
    }
}

vendorOperator -> platform.controlPlane "Operates, when hosted" "" {
    properties {
        "decisions" "D22, D45"
    }
}
