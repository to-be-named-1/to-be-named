# 3. IR and execution engines

Date: 2026-10-11
Applies to: platform.controlPlane

## Status

Accepted

## Context

The IR is the anti-corruption layer: each backend reports failure, resource limits and cancellation differently, and all of it must be normalized into one vocabulary.

## Decision

The IR is custom to the platform and compiles down to existing engines and backends. No external engine's model becomes the domain model.

- **Dispatch.** The platform's own orchestrator owns control flow and state and dispatches individual execution units to backends. Compiling a whole workflow into Argo or Airflow is offered as an export for workflows without loops, not as the execution path.
- **Follows.** The IR has a formal spec and schema version from day one, with migrations, because users commit it to git.
