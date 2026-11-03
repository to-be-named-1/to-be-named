# 61. Logging and configuration

Date: 2026-10-29
Applies to: platform

## Status

Accepted

## Context

The control plane and the agent are long-running Go processes that operators install and configure themselves, on a single machine or on Kubernetes ([D22](0022-deployment-topologies.md), [D47](0047-control-plane-structure.md)). Units are not configured that way: a unit fetches its specification from the agent's local endpoint, with its resources, credential scopes and secret references, and secrets are resolved in the data plane ([D40](0040-protocol-between-the-control-and-data-planes.md)). Telemetry is best effort and goes to a configurable sink, a customer may keep logs in its own environment because they may hold sensitive content, and credentials never appear in them ([D22](0022-deployment-topologies.md), [D40](0040-protocol-between-the-control-and-data-planes.md), [CORE 7.3]({workspace}/documentation#3)). The observability stack that ships and stores logs is not chosen; every process still has to write them, in one form, before any of it is.

The unit runtime shares its Python environment with the code of the nodes it runs, so every dependency the runtime adds narrows the versions authors can install.

## Decision

The Go processes read their settings from defaults, a file and the environment, in that order; every process writes structured logs to standard error in one shape.

- **Who is configured.** The control plane and the agent read configuration. Units and derivation units read none beyond the address of the agent's endpoint, which the agent passes them; everything else arrives in the unit specification ([D40](0040-protocol-between-the-control-and-data-planes.md)).
- **Sources.** Defaults set in code, then an optional YAML file named by the one command-line flag, `--config`, then environment variables; each source overrides the one before it. The file is read strictly: a key that no setting defines is an error. Every invalid setting is reported, together, when the process starts, and the process does not start.
- **Names.** Keys in the file are snake_case. An environment variable's name is derived from its key, prefixed with the binary's name: `database.url` is `CONTROLPLANE_DATABASE_URL`, so the names do not change with the product's.
- **Secrets.** A secret is never read from the file. It comes from its environment variable or from a file whose path is given in the variable of the same name suffixed `_FILE`, as Kubernetes and Docker mount secrets. A secret prints as `[redacted]` in logs and in any text the process writes.
- **No named modes.** No setting selects a mode such as development or production that changes several behaviors at once; each behavior, such as the log format, is a setting of its own ([D58](0058-behavior-follows-properties.md)). The binaries read no `.env` files.
- **Go logging.** `log/slog`, writing one JSON object per line to standard error, or text as a setting. Components receive their logger; the attributes of a request or attempt, such as `tenant_id`, `project_id`, `run_id`, `attempt_id` and `request_id`, are added from its context to every line written for it. Keys are snake_case.
- **Python logging.** The standard library's `logging`, with a JSON formatter of the platform's own that writes the same keys as the Go processes: `time`, `level` and `msg`, followed by the attributes. The unit runtime configures it; the SDK, a library, never configures handlers.
- **Shipping.** Processes only write to standard error. Collecting, shipping and storing logs is left to the observability stack ([D40](0040-protocol-between-the-control-and-data-planes.md)).
- **Libraries.** goccy/go-yaml, already used for the IR, reads the file; caarlos0/env reads the environment. Both versions are fixed in `go.mod` ([D60](0060-code-layout-and-tooling.md)).

## Consequences

- One settings struct per binary is the whole schema of its configuration, with its defaults and its checks.
- A setting misspelled in the file stops the process instead of being ignored.
- Logs from Go and Python processes can be read by one parser.
- The unit runtime adds no dependency for logging.

## Rejected alternatives

- Environment variables alone. Nested settings, such as pools or timings, are hard to write and review as flat variables.
- A configuration library that merges providers by key paths, such as koanf or viper. They duplicate what one struct with tags already states, and viper lowercases keys and brings many dependencies.
- An environment name, such as `ENV=dev`, choosing files and behaviors. It hides which behaviors change, and "environment" already names the IR's environment documents.
- Loading `.env` files in the binaries. Operators' environment managers, Compose and Kubernetes already supply variables, and a file read at start-up silently overrides them.
- zap or zerolog. Faster, but `log/slog` is the interface other libraries accept, adds no dependency, and its speed suffices.
- structlog, loguru or python-json-logger in units. Each would constrain the dependencies of authors' code, and node code and the libraries it uses already log through the standard library.

## Follow-ups

- How the output and logs of node code reach the agent, with the agent–unit contract ([D40](0040-protocol-between-the-control-and-data-planes.md)).
- Configuration of the CLI and the SDK, with their designs (design agenda).
- Metrics and tracing, with the observability stack (design agenda).
