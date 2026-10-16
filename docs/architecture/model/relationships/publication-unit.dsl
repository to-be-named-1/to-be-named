// Relationships from publication unit.

platform.publicationUnit -> platform.agent "Fetches its specification and reports through" "ConnectRPC, local endpoint" {
    properties {
        "decisions" "D40, D55"
    }
}

platform.publicationUnit -> objectStorage "Writes table metadata to" "S3 API" {
    properties {
        "decisions" "D55"
    }
}

platform.publicationUnit -> lakehouseCatalog "Commits table snapshots and repoints partitions through" "Iceberg, Delta or Hive metastore API" {
    properties {
        "decisions" "D51, D55"
    }
}
