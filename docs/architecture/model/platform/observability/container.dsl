observability = container "Observability service" "Receives logs, metrics and node events, redacts secrets on ingestion, serves the live log tail and the searchable archive, and raises alerts." "" {
    properties {
        "decisions" "D21, D40"
    }
}
