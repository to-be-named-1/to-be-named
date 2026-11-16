// Relationships from the maintenance unit's components.

platform.maintenanceUnit.probe -> platform.agent "Fetches its specification and returns probed positions through" "ConnectRPC, local endpoint" {
    properties {
        "decisions" "D40, D49"
    }
}

platform.maintenanceUnit.probe -> dataSources "Asks for the current version or position of" "" {
    properties {
        "decisions" "D49"
    }
}

platform.maintenanceUnit.projection -> platform.agent "Fetches its specification and reports through" "ConnectRPC, local endpoint" {
    properties {
        "decisions" "D40, D44"
    }
}

platform.maintenanceUnit.projection -> objectStorage "Writes Iceberg metadata to" "S3 API" {
    properties {
        "decisions" "D42, D44"
    }
}

platform.maintenanceUnit.projection -> platform.bundledObjectStorage "Writes Iceberg metadata to" "S3 API" {
    properties {
        "decisions" "D42, D44"
    }
}

platform.maintenanceUnit.projection -> icebergCatalog "Registers Iceberg snapshots in" "REST or SQL catalog" {
    properties {
        "decisions" "D44"
    }
}

platform.maintenanceUnit.publication -> platform.agent "Fetches its specification and reports through" "ConnectRPC, local endpoint" {
    properties {
        "decisions" "D40, D55"
    }
}

platform.maintenanceUnit.publication -> objectStorage "Writes table metadata to" "S3 API" {
    properties {
        "decisions" "D55"
    }
}

platform.maintenanceUnit.publication -> lakehouseCatalog "Commits table snapshots and repoints partitions through" "Iceberg, Delta or Hive metastore API" {
    properties {
        "decisions" "D51, D55"
    }
}

platform.maintenanceUnit.sampleBuilding -> platform.agent "Fetches its specification and reports through" "ConnectRPC, local endpoint" {
    properties {
        "decisions" "D40, D50"
    }
}

platform.maintenanceUnit.sampleBuilding -> objectStorage "Reads inputs from and writes samples to" "S3 API" {
    properties {
        "decisions" "D50"
    }
}

platform.maintenanceUnit.sampleBuilding -> platform.bundledObjectStorage "Reads inputs from and writes samples to" "S3 API" {
    properties {
        "decisions" "D50"
    }
}

platform.maintenanceUnit.sampleBuilding -> dataSources "Reads external sources at their probed version from" "" {
    properties {
        "decisions" "D49, D50"
    }
}

platform.maintenanceUnit.commitRecovery -> platform.agent "Submits staged commit requests and completion records through" "ConnectRPC, local endpoint" {
    properties {
        "decisions" "D64, D65"
    }
}

platform.maintenanceUnit.commitRecovery -> objectStorage "Reads staged commit requests and completion records from" "S3 API" {
    properties {
        "decisions" "D64, D65"
    }
}

platform.maintenanceUnit.commitRecovery -> platform.bundledObjectStorage "Reads staged commit requests and completion records from" "S3 API" {
    properties {
        "decisions" "D64, D65"
    }
}

platform.maintenanceUnit.storageDeletion -> platform.agent "Fetches its specification and confirms deletions through" "ConnectRPC, local endpoint" {
    properties {
        "decisions" "D64"
    }
}

platform.maintenanceUnit.storageDeletion -> objectStorage "Deletes collected files from" "S3 API" {
    properties {
        "decisions" "D42, D64"
    }
}

platform.maintenanceUnit.storageDeletion -> platform.bundledObjectStorage "Deletes collected files from" "S3 API" {
    properties {
        "decisions" "D42, D64"
    }
}

platform.maintenanceUnit.logReading -> platform.agent "Returns log chunks through" "ConnectRPC, local endpoint" {
    properties {
        "decisions" "D65"
    }
}

platform.maintenanceUnit.logReading -> objectStorage "Reads log chunks from" "S3 API" {
    properties {
        "decisions" "D65"
    }
}

platform.maintenanceUnit.logReading -> platform.bundledObjectStorage "Reads log chunks from" "S3 API" {
    properties {
        "decisions" "D65"
    }
}

platform.maintenanceUnit.integrityCheck -> platform.agent "Fetches its specification and reports differences through" "ConnectRPC, local endpoint" {
    properties {
        "decisions" "D64"
    }
}

platform.maintenanceUnit.integrityCheck -> objectStorage "Compares files with their manifests in" "S3 API" {
    properties {
        "decisions" "D4, D42, D51, D64"
    }
}

platform.maintenanceUnit.integrityCheck -> platform.bundledObjectStorage "Compares files with their manifests in" "S3 API" {
    properties {
        "decisions" "D4, D42, D64"
    }
}
