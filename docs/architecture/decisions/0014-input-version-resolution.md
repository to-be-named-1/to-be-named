# 14. Input version resolution

Date: 2026-10-11
Applies to: platform.controlPlane

## Status

Accepted

Amended by [42. Catalog persistence](0042-catalog-persistence.md)
Amended by [49. Source probes](0049-source-probes.md)

## Context

The reasoning on nested workflows inlined and on quality-gate holds being bounded, in [D31](0031-execution-state-model.md), also cites this decision.

## Decision

A run resolves the versions of all its inputs once, when it starts, records them, and every node in the run reads exactly those versions. Because every input is resolved at the same instant, a run reads its inputs under snapshot isolation.

- **Pinning.** Any input may instead be pinned to a specific version or snapshot, for example for model training or a reproduction study. Pinned versions are recorded in the same way.
- **Coherent reads.** A user may declare coherent reads for a workflow, with per-input override. The resolver then selects versions that are consistent along lineage — where a run reads both a dataset and something derived from it, the derived version is chosen first and the upstream version that produced it is used. If no coherent set exists, the run fails with an explanation or follows its stale-input policy ([D16](0016-input-readiness-and-degraded-outputs.md)). This is a configuration of the read model, not a separate feature.
- **Completeness.** Snapshot isolation guarantees a consistent read, not consistent business state. Where inputs must be complete for an interval, partition completion markers (CORE 3.10) and the consumer's stale-input policy ([D16](0016-input-readiness-and-degraded-outputs.md)) apply.
- **Reruns.** Two distinct actions: **re-execute as recorded** reads the originally resolved versions; **run again on current data** resolves afresh. They are presented separately and never conflated.
- **Retention.** Versions resolved by a run still in progress are protected from garbage collection until the run finishes, so a long run cannot lose its own inputs.
- **Mechanism.** Recorded by [D42](0042-catalog-persistence.md): inputs are resolved inside one repeatable-read transaction and recorded as version identifiers, never as a cutoff.
- **External sources.** Amended by [D49](0049-source-probes.md): the versions and positions of external sources that can be read as of a probed position are fixed at run start by a source probe and recorded with the internal inputs, so every node of the run reads the same version. Sources that cannot be pinned are recorded as read.
