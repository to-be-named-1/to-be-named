# 12. Streaming readiness

Date: 2026-10-11
Applies to: platform.controlPlane, platform.database, platform.agent, platform.unitRuntime, platform.observability

## Status

Accepted

## Context

The reasoning on phase separate from outcome, in [D31](0031-execution-state-model.md), and on loops always bounded, in [D46](0046-control-flow-constructs.md), also cites this decision.

## Decision

Streaming is excluded from the initial scope ([D6](0006-streaming.md)), but the core model is built so that it can be added without rework. The risk is not missing features; it is assumptions that only hold for finite work being written into schemas, interfaces and state machines. Every design decision is tested against three questions: does it assume execution **terminates**, does it assume input is a **finite snapshot**, and does it assume time means the **wall clock of the run**?

- **Seam 1.** A finite run is one kind of execution, not the only kind. Identity, permissions, monitoring and API routes sit on a neutral execution concept; status vocabularies and schemas are not constrained to terminal states (no mandatory completion timestamp, no success-or-failure-only enum).
- **Seam 2.** The scheduler does not assume tasks end. Health is derived from lease renewal rather than exit status, so an indefinitely running task is representable.
- **Seam 3.** Node types declare which execution modes they support. Every entry reads `[batch]` initially; the field prevents a later restructuring of the palette and allows validation to report a missing streaming implementation.
- **Seam 4.** Every source read records the **range of positions consumed** — snapshot, object version or timestamp now, offsets later — rather than naming a file. Incremental extraction ([DE 1.2]({workspace}/documentation#4)) requires this regardless, and provenance then generalizes to window and offset lineage unchanged.
- **Seam 5.** A dataset version is not defined as a snapshot of a finite table. Datasets are append-only sequences with positions, of which a snapshot is one case and a retained topic another.
- **Seam 6.** Event time is distinguished from processing time. Optional event-time metadata on datasets — timestamp column, allowed lateness — is used by micro-batch immediately and by streaming unchanged.
- **Seam 7.** Reproducibility tiers are defined in terms of **replayable recorded inputs**, not retained files, so retained artifacts and offsets still within a retention window are treated identically, including tier decay on expiry.
- **Seam 8.** Caching is a policy applied to finite outputs behind a strategy interface, not an assumption embedded in dispatch. A unit may legitimately have no cache policy.
- **Seam 9.** The backend interface manages a lifecycle — submit, observe, cancel — with room for optional operations such as upgrade and state snapshot, so a long-lived execution is another backend implementation rather than a new subsystem.
- **Seam 10.** Task metrics are recorded as time series rather than end-of-run summaries, so lag, watermark skew and backpressure later use the same storage and views.
- **Excluded.** No savepoint or upgrade machinery, state schema evolution, watermark or lateness configuration, exactly-once sink protocols, offset management or streaming connectors. No unified batch-and-streaming abstraction: committing to the intersection of two execution models before either is understood is itself a cost.
- **Cost.** Most seams are field additions and naming discipline. Two require deliberate design: the execution concept (Seam 1) and the input-range model (Seam 4). Untested seams tend to be subtly wrong, so a minimal long-running execution should be implemented as a proof before the model is considered settled. The execution concept of Seam 1 is recorded in [D31](0031-execution-state-model.md).

## Follow-ups

- A minimal long-running execution, to be built as a proof that the streaming seams hold.
