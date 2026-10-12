// Relationships from agent.

platform.agent -> platform.controlPlane "Claims work from, renews leases with and requests commits from" "ConnectRPC over HTTPS, outbound only" {
    properties {
        "decisions" "D40, D44, D48"
    }
}

platform.agent -> dockerEngine "Starts, observes and stops unit containers on" "Docker API" {
    properties {
        "decisions" "D12, D29"
    }
}

platform.agent -> kubernetes "Submits, observes and cancels unit jobs on" "Kubernetes API" {
    properties {
        "decisions" "D12, D29"
    }
}

platform.agent -> hpcScheduler "Submits, observes and cancels unit jobs on" "Slurm" {
    properties {
        "decisions" "D12, D22"
    }
}

platform.agent -> cloudBatch "Submits, observes and cancels unit jobs on" "" {
    properties {
        "decisions" "D12, D22"
    }
}

platform.agent -> secretManager "Resolves secret references from" "" {
    properties {
        "decisions" "D40"
    }
}

platform.agent -> platform.secretStore "Resolves secret references from" "" {
    properties {
        "decisions" "D40"
    }
}

platform.agent -> credentialIssuer "Mints short-lived storage credentials with" "" {
    properties {
        "decisions" "D22, D40"
    }
}

platform.agent -> objectStorage "Deletes collected files from, and checks integrity in" "S3 API" {
    properties {
        "decisions" "D42"
    }
}

platform.agent -> platform.bundledObjectStorage "Deletes collected files from, and checks integrity in" "S3 API" {
    properties {
        "decisions" "D42"
    }
}

platform.agent -> observabilitySink "Forwards logs and metrics to" "" {
    properties {
        "decisions" "D21, D40"
    }
}
