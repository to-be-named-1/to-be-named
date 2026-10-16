# 6. Streaming

Date: 2026-10-11
Applies to: platform

## Status

Accepted

## Context

As first recorded, such a long-lived execution was called a deployment; that word now refers to workflow changes reaching production.

## Decision

Batch only at first; micro-batch next (frequent scheduled runs over incremental data); managed long-running streaming jobs possibly later. A native streaming runtime is out of scope.

- **Follows.** Micro-batch needs no new execution model; it builds on incremental extraction state and logical intervals.
- **Follows.** The domain model leaves room for a long-lived execution next to finite runs, without building it now. The seams that keep this option open are recorded in [D12](0012-streaming-readiness.md).
