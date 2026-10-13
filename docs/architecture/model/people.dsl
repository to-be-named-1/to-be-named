// People: defined by how they use the platform; the roles of D45 they need are recorded as properties.

workflowAuthor = person "Workflow author" "Analyst, researcher, data scientist or engineer who builds workflows, tries them on samples and in sandboxes, and commits them." {
    properties {
        "roles" "Developer"
        "decisions" "D41, D45, D50"
    }
}

operator = person "Operator" "Triggers, backfills, pauses and cancels runs and materialization requests, and monitors them." {
    properties {
        "roles" "Operator"
        "decisions" "D20, D24, D31, D45"
    }
}

projectMaintainer = person "Project maintainer" "Manages a project's settings, environment bindings and membership, approves changes to governed fields and deploys." {
    properties {
        "roles" "Maintainer"
        "decisions" "D41, D45"
    }
}

datasetOwner = person "Dataset owner" "Sets a dataset's contract, classification, retention and freshness, releases quarantined versions and approves gated publication." {
    properties {
        "roles" "dataset.manage"
        "decisions" "D4, D31, D45"
    }
}

tenantAdmin = person "Tenant administrator" "Manages members, service accounts, projects, agent pools, connections, storage targets, catalogs, quotas and fair-share weights." {
    properties {
        "roles" "Admin"
        "decisions" "D43, D45, D47"
    }
}

auditor = person "Auditor" "Reads the audit trail and all metadata, but no data content." "Commercial" {
    properties {
        "roles" "Auditor"
        "decisions" "D5, D45"
    }
}

dataConsumer = person "Data consumer" "Reads managed datasets as tables with their own query engines, without using the platform directly." {
    properties {
        "decisions" "D42, D44"
    }
}

infrastructureOperator = person "Infrastructure operator" "Customer staff who install and upgrade a self-hosted platform, its agents and the backends they drive." {
    properties {
        "decisions" "D22, D40"
    }
}

vendorOperator = person "Vendor operator" "Vendor staff who operate the hosted control plane; support access to tenant records is break-glass only." "Commercial" {
    properties {
        "decisions" "D22, D45"
    }
}
