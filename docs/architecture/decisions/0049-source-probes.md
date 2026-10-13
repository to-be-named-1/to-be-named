# 49. Source probes

Date: 2026-10-11
Applies to: platform.controlPlane, platform.agent, platform.unitRuntime, platform.probeUnit, dataSources

## Status

Accepted

Amends [14. Input version resolution](0014-input-version-resolution.md)
Amends [18. Format types, plugin implementations and bindings](0018-format-types-plugin-implementations-and-bindings.md)
Amends [35. Ephemeral extraction](0035-ephemeral-extraction.md)
Amends [37. Incremental extraction state](0037-incremental-extraction-state.md)
Amends [40. Protocol between the control and data planes](0040-protocol-between-the-control-and-data-planes.md)
Amended by [51. Adoption of existing data](0051-adoption-of-existing-data.md)

## Context

**Source probes in the data plane** (D49). The control plane holds no credentials, runs no plugin code and, when hosted, has no route into the customer's network, so it cannot ask an external source for its version. Discovering versions when units read let two units of one run read different snapshots, left nodes reading external sources without keys before the run, and let retries read different data. A probe unit fixes them at run start; a probe inside the agent would tie connector fixes to agent upgrades, as [D44](0044-minimum-technology-stack.md) found for the projection.

## Decision

External sources are resolved at run start by source probes run in the data plane, so that a run reads each external source at one version and nodes reading it have keys before the run.

- **Why in the data plane.** The control plane holds no credentials ([D40](0040-protocol-between-the-control-and-data-planes.md)), runs no plugin code ([D21](0021-architecture-planes.md)) and, when hosted, has no route into the customer's network ([D22](0022-deployment-topologies.md)), so it cannot ask an external source for its version. A probe runs where credentials are minted and returns only metadata.
- **Probe.** A platform maintenance unit that calls an optional `probe` function on each connector ([D18](0018-format-types-plugin-implementations-and-bindings.md)), returning the source's current version or position without reading its data. As a unit it reaches every deployment through the image the control plane selects, without waiting for agent upgrades, and reuses leases, credentials and retries ([D44](0044-minimum-technology-stack.md)). Probes are batched across runs per pool and offered to the pool that the project's environment bindings associate with the source's connection ([D41](0041-ir-text-form-round-trip-and-structure.md)).
- **At input resolution.** The run stays in its resolving sub-state, requests probes for its external inputs and waits; it then resolves its internal inputs in one repeatable-read transaction and records both together ([D14](0014-input-version-resolution.md), [D47](0047-control-plane-structure.md)). Probes run in parallel, so their results are close in time but not atomic across systems. If a probe fails, the infrastructure retry budget applies ([D31](0031-execution-state-model.md)); if it keeps failing, the source counts as not ready and the input's readiness policy decides ([D16](0016-input-readiness-and-degraded-outputs.md)).
- **What can be pinned.** A probe helps only where the unit can read as of the position it returns: an Iceberg snapshot, read by snapshot identifier; versioned objects in S3, read by version identifier; a Snowflake table, read with `AT (TIMESTAMP => …)` within its Time Travel retention; a set of immutable files; a log offset for change data capture; and the upper bound of watermark polling, from the source's clock ([D37](0037-incremental-extraction-state.md)). Operational databases without time travel, API sync tokens and unversioned tables cannot be pinned; they are recorded as read, capped at Traceable and not cacheable ([D35](0035-ephemeral-extraction.md)).
- **Reads.** The unit specification carries each probed position, and units read as of it ([D40](0040-protocol-between-the-control-and-data-planes.md)); the read record keeps the position used ([D42](0042-catalog-persistence.md)). If the position has expired before the unit reads, for example beyond a warehouse's time-travel retention, the attempt fails with that reason.
- **Default.** On wherever a source can be read as of the probed position; an author may opt a source out. This passes the test of [D36](0036-data-engineering-practice-first-reproducibility-by-choice.md): probes serve consistency within a run, deterministic retries and caching, at the cost of one small unit per run rather than storage.
- **Sensing.** The reconciler runs probes periodically for external sources that drive triggers (CORE 3.2, DE 1.6) or carry a freshness expectation (DE 4.2), and each external source declaration keeps its last probed position.
- **Adoption.** Three further kinds of probe serve the adoption of existing data ([D51](0051-adoption-of-existing-data.md)): the layout check, which lists a dataset's root and matches every file against its path template; the baseline scan, which lists existing files with their sizes, ETags and modification times, or reads a table's current state; and the observation of an external producer, which records each new version it sees without reading the data.
- **What it gives.** Every unit of a run reads an external source at one version ([D14](0014-input-version-resolution.md)); nodes reading external sources have input-addressed keys before the run, so expected reuse covers them ([D8](0008-cache-keying.md), [D47](0047-control-plane-structure.md)); retries read the same version or range; and an incremental range is recorded whole before it is read ([D37](0037-incremental-extraction-state.md)).
- **Amends.** [D14](0014-input-version-resolution.md): the snapshot covers external sources that can be read as of a probed position. [D18](0018-format-types-plugin-implementations-and-bindings.md): connectors gain an optional `probe` function. [D35](0035-ephemeral-extraction.md): the version of such a source is fixed at run start rather than discovered at read time. [D37](0037-incremental-extraction-state.md): the end position of an incremental range is fixed at resolution. [D40](0040-protocol-between-the-control-and-data-planes.md): probes are a further kind of offered work.

## Rejected alternatives

- Discovering versions only when units read, which let two units of one run read different snapshots, left such nodes without keys before the run and let retries read different data.
- Probing inside the agent, which would duplicate connector logic in Go and tie its fixes to customers' agent upgrades, as [D44](0044-minimum-technology-stack.md) found for the projection; native probes for a few built-in source kinds remain possible if measured latency calls for them.

## Follow-ups

- Native probes in the agent for built-in source kinds, if measured probe latency matters; how the pool for a probe is chosen when a source's connection is bound to several pools.
