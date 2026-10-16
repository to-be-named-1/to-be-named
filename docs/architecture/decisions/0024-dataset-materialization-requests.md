# 24. Dataset materialization requests

Date: 2026-10-11
Applies to: platform.controlPlane, platform.webApp, operator

## Status

Accepted

## Decision

Alongside running a workflow, a user may ask for a dataset to be made current through a given time. The reconciler derives and runs the minimum work required. In the first release such requests are confined to a single project.

- **Two entry points.** **Imperative**: run workflow W for interval X. **Declarative**: make dataset Y current through time T, where the reconciler decides what runs from dataset state, dependency functions and readiness policies.
- **Planning.** The planner operates on the dataset graph of the project, which may span several workflows.
- **Grouping.** A materialization request is a first-class entity grouping every run it causes, so that the reason any run occurred can be traced back to the request that caused it.
- **Interface.** The catalog offers refresh actions with explicit build modes — only this dataset; upstream where modified; all upstream; downstream — and shows stale state.
- **Later.** Requests that cross project boundaries, where execution rights must be resolved against the producing team's policies, and freshness policies that the reconciler enforces automatically in place of schedules.

## Follow-ups

- Cross-project materialization requests and automatically enforced freshness policies.
