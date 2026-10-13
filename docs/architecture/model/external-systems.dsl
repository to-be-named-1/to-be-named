// External systems: one element per kind of system; products appear only in descriptions.

gitHost = softwareSystem "Git host" "Holds the history and review of git-connected projects' workflow and dataset definitions, for example GitHub or GitLab." "External" {
    properties {
        "decisions" "D41, D45"
    }
}

identityProvider = softwareSystem "Identity provider" "Authenticates people through OpenID Connect, or through SAML in the commercial edition." "External" {
    properties {
        "decisions" "D5, D45, D53"
    }
}

objectStorage = softwareSystem "Object storage" "Customer or platform object storage holding artifacts, staged outputs and managed datasets, for example Amazon S3, Google Cloud Storage or Azure Blob Storage." "External, Object Storage" {
    properties {
        "decisions" "D4, D23, D42, D51"
    }
}

icebergCatalog = softwareSystem "Iceberg catalog" "REST or SQL catalog in which projected Iceberg tables are registered for external engines." "External" {
    properties {
        "decisions" "D42, D44"
    }
}

queryEngines = softwareSystem "External query engines" "Engines that read managed datasets as Iceberg tables, for example DuckDB, Spark, Trino or PyIceberg." "External" {
    properties {
        "decisions" "D44"
    }
}

dockerEngine = softwareSystem "Docker engine" "Container runtime of a single-machine installation." "External"

kubernetes = softwareSystem "Kubernetes cluster" "Cluster on which units run as pods." "External" {
    properties {
        "decisions" "D22"
    }
}

hpcScheduler = softwareSystem "HPC scheduler" "Slurm cluster on which units run as jobs, commonly through Apptainer." "External" {
    properties {
        "decisions" "D22"
    }
}

cloudBatch = softwareSystem "Cloud batch service" "Managed batch service on which units run as jobs." "External" {
    properties {
        "decisions" "D22"
    }
}

containerRegistry = softwareSystem "Container registry" "Holds the images units run, referenced by digest, built from declared dependencies." "External" {
    properties {
        "decisions" "D22"
    }
}

secretManager = softwareSystem "Secret manager" "The customer's secret manager, from which the agent resolves secret references." "External" {
    properties {
        "decisions" "D40"
    }
}

credentialIssuer = softwareSystem "Cloud credential issuer" "Issues the short-lived storage credentials the agent mints for each unit, for example AWS STS or workload identity." "External" {
    properties {
        "decisions" "D22, D40"
    }
}

dataSources = softwareSystem "External data sources" "Operational databases, APIs, files and object stores that workflows read without the platform owning them." "External" {
    properties {
        "decisions" "D4, D35, D37, D49, D51"
    }
}

sideEffectTargets = softwareSystem "Side-effect targets" "External systems that nodes write to, send messages to or trigger." "External" {
    properties {
        "decisions" "D40, D50"
    }
}

warehouses = softwareSystem "Warehouses" "Postgres and Snowflake, to which relational work is pushed down and from which reduced data is extracted." "External" {
    properties {
        "decisions" "D25, D28"
    }
}

customerObservability = softwareSystem "Customer observability stack" "The customer's own log and metrics stores, to which telemetry is routed when it is kept in the customer's environment." "External" {
    properties {
        "decisions" "D22, D40"
    }
}

notificationChannels = softwareSystem "Notification channels" "Email, chat and webhooks that receive alerts." "External"

ciSystem = softwareSystem "CI system" "Continuous integration that starts sample and development runs as a service account." "External" {
    properties {
        "decisions" "D45, D50"
    }
}
