// Relationships from external systems.

ciSystem -> platform.controlPlane "Starts sample and development runs through the API of" "ConnectRPC over HTTPS" {
    properties {
        "decisions" "D45, D50"
    }
}

queryEngines -> icebergCatalogue "Looks up projected tables in" "" {
    properties {
        "decisions" "D44"
    }
}

queryEngines -> objectStorage "Reads the files of projected tables from" "" {
    properties {
        "decisions" "D44"
    }
}

queryEngines -> platform.bundledObjectStorage "Reads the files of projected tables from" "" {
    properties {
        "decisions" "D44"
    }
}

dockerEngine -> containerRegistry "Pulls images by digest from" "" {
    properties {
        "decisions" "D22"
    }
}

kubernetes -> containerRegistry "Pulls images by digest from" "" {
    properties {
        "decisions" "D22"
    }
}

hpcScheduler -> containerRegistry "Pulls images by digest from" "" {
    properties {
        "decisions" "D22"
    }
}

cloudBatch -> containerRegistry "Pulls images by digest from" "" {
    properties {
        "decisions" "D22"
    }
}
