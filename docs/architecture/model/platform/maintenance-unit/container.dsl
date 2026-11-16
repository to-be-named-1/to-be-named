maintenanceUnit = container "Maintenance unit" "Runs the platform's own jobs in the data plane, offered and leased like any unit; each job is a component." "Python" "Maintenance unit" {
    properties {
        "decisions" "D65"
    }

    probe = component "Probe" "Asks external sources for their current version or position and their schema when a run starts or a dataset is registered, checks and scans existing data at adoption, and observes external producers." "Python" {
        properties {
            "decisions" "D49, D51, D62, D63"
        }
    }
    projection = component "Projection" "Writes Iceberg metadata for every version of a managed dataset that becomes current, and registers it in a catalog." "Python, PyIceberg" {
        properties {
            "decisions" "D42, D44"
        }
    }
    publication = component "Publication" "Commits versions made current by the platform to storage targets that have their own commit: Iceberg and Delta tables and Hive-style tables." "Python" {
        properties {
            "decisions" "D15, D55"
        }
    }
    sampleBuilding = component "Sample building" "Builds and stores the samples that sample runs read." "Python, DuckDB" {
        properties {
            "decisions" "D50"
        }
    }
    commitRecovery = component "Commit recovery" "Completes an attempt whose container ended without its results acknowledged, by submitting what the attempt staged: its completion record, commit requests and checkpoint commits." "Python" {
        properties {
            "decisions" "D64, D65"
        }
    }
    storageDeletion = component "Storage deletion" "Deletes the files that collection marking left unreferenced, with credentials scoped to them, and confirms each deletion." "Python" {
        properties {
            "decisions" "D64"
        }
    }
    integrityCheck = component "Integrity check" "Compares the files of chosen dataset versions with their manifests, by size, ETag and modification time or by full digests, and reports files changed or deleted out of band." "Python" {
        properties {
            "decisions" "D64"
        }
    }
    logReading = component "Log reading" "Reads the log chunks of a finished attempt from its staging, for pools whose storage browsers cannot reach." "Python" {
        properties {
            "decisions" "D65"
        }
    }
}
