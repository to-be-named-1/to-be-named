unitRuntime = container "Unit runtime" "Runs one execution unit's engine segments in a container: reads inputs, runs nodes, calls format plugins, stages outputs and requests the commit." "Python, Ibis on DuckDB, Polars" {
    properties {
        "decisions" "D25, D27, D32, D40, D44, D49"
    }
}
