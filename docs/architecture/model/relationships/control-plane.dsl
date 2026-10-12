// Relationships from control plane.

platform.controlPlane -> platform.database "Reads from and writes to, in tenant-scoped transactions" "SQL over pgx" {
    properties {
        "decisions" "D42, D45, D47"
    }
}

platform.controlPlane -> gitHost "Pushes authors' commits to, and watches the deploy branch of" "HTTPS" {
    properties {
        "decisions" "D45"
    }
}

platform.controlPlane -> identityProvider "Authenticates people through" "OpenID Connect" {
    properties {
        "decisions" "D45"
    }
}

platform.controlPlane -> notificationChannels "Sends alerts to" ""
