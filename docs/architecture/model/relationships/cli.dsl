// Relationships from cli.

platform.cli -> platform.controlPlane "Calls the API of" "ConnectRPC over HTTPS" {
    properties {
        "decisions" "D44"
    }
}

platform.cli -> objectStorage "Uploads large files directly to" "S3 API over HTTPS" {
    properties {
        "decisions" "D4"
    }
}

platform.cli -> platform.bundledObjectStorage "Uploads large files directly to" "S3 API over HTTPS" {
    properties {
        "decisions" "D4"
    }
}
