// Relationships from web app.

platform.webApp -> platform.controlPlane.apiLayer "Calls the API of" "ConnectRPC over HTTPS" {
    properties {
        "decisions" "D44, D45"
    }
}

platform.webApp -> objectStorage "Uploads files directly to, through pre-signed URLs" "S3 API over HTTPS" {
    properties {
        "decisions" "D4, D21"
    }
}

platform.webApp -> platform.bundledObjectStorage "Uploads files directly to, through pre-signed URLs" "S3 API over HTTPS" {
    properties {
        "decisions" "D4, D21"
    }
}
