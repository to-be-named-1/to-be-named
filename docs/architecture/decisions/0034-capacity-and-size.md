# 34. Capacity and size

Date: 2026-10-11
Applies to: platform.controlPlane, platform.unitRuntime, tenantAdmin

## Status

Accepted

Amends [25. Processing engines and runtimes](0025-processing-engines-and-runtimes.md)
Amended by [47. Control-plane structure](0047-control-plane-structure.md)
Amended by [57. Node-type contract](0057-node-type-contract.md)

## Context

**No declared maximum dataset size** (D34). A size limit on a dataset was rejected because capacity depends on the operation and on the unit's slice of the data, not on the dataset as a whole. Observed statistics, memory classes and backend ceilings give the planner what it needs, and the same check later chooses between engines at the same location.

The reasoning on engine selection by location, not size, in [D25](0025-processing-engines-and-runtimes.md), also cites this decision.

## Decision

No maximum size is declared on datasets. Capacity is not a property of a dataset but of the operation, the data and the resources of the unit that runs it: a filter streams through any volume, a large join or aggregation is bounded by disk and time once DuckDB spills, and a non-spilling operation is bounded by memory. Because most units process one partition or one bucket ([D13](0013-partitioning-intervals-and-dataset-ownership.md), [D25](0025-processing-engines-and-runtimes.md)), the size that matters is each unit's input slice. The planner therefore observes sizes and checks them against capacity.

- **Observed sizes.** Byte and row counts per partition are mandatory statistics on every artifact manifest ([D23](0023-artifact-storage-layout.md)). Sizes of outputs not yet produced are estimated from upstream statistics or the previous run, and marked unknown where neither exists.
- **Memory class.** Every node has a memory class — streaming, blocking and spilling, or blocking and non-spilling — derived from its compiled expression where it is an Ibis or SQL plan, otherwise blocking and non-spilling by default, and declared by its node type only as a hint ([D57](0057-node-type-contract.md)).
- **Capacity ceilings.** Administrators declare, per backend, the largest memory and ephemeral disk a single unit may be granted.
- **Capacity check.** The planner estimates each unit's working set from observed sizes and memory classes and compares it with the ceiling. Where it does not fit, the planner repartitions and fans out if the node declares a grouping key ([D25](0025-processing-engines-and-runtimes.md), [CORE 2.26]({workspace}/documentation#3)), otherwise requests a larger allocation up to the ceiling, and otherwise flags the unit before the run with its reason. The result is recorded in the plan like any placement ([D26](0026-placement-constraints.md), Seam 3). This replaces the informal single-node guideline of [D25](0025-processing-engines-and-runtimes.md).
- **Warn, not refuse.** Estimates are approximate, so the check warns rather than refusing. A unit that does exceed its allocation fails as resource exhausted ([D31](0031-execution-state-model.md)), and memory escalation ([S8]({workspace}/documentation#7.8)) may be added later.
- **Spill disk.** DuckDB's temporary directory is placed on the unit's ephemeral volume, with its maximum size set from the unit's allocation, as memory and thread limits are ([D25](0025-processing-engines-and-runtimes.md)), so that a spilling unit fails cleanly rather than being evicted.
- **Calibration.** Peak memory and spill volume are recorded per task run as time series ([CORE 4.2]({workspace}/documentation#3), [CORE 4.6]({workspace}/documentation#3)) and used to refine estimates; the same measurements serve the cost-informed fusion policy ([D33](0033-automatic-fusion.md)).
- **Later engines.** [D25](0025-processing-engines-and-runtimes.md)'s rule that location, not size, selects the engine held while the only alternative to in-process work was a warehouse, which is a different location. An engine that reads the same files as the in-process engines, such as Spark, can only be chosen by capacity. When one is added, the selection precedence becomes: hard constraints ([D26](0026-placement-constraints.md)), dialect capability and connection policy ([D28](0028-warehouse-connection-policy-and-plan-pinning.md)), an explicit override among the engines that remain ([D57](0057-node-type-contract.md)), data location, then capacity among the engines at that location. The planner records the reason, and plan pinning ([D28](0028-warehouse-connection-policy-and-plan-pinning.md)) protects production workflows from unannounced moves.
- **Estimation.** Settled by [D47](0047-control-plane-structure.md): a unit's input slice is sized from its manifests, including uncompressed sizes recorded from Parquet footers, with an expansion factor per type; sizes are propagated through its nodes from the per-node statistics of earlier runs ([CORE 6.6]({workspace}/documentation#3)), otherwise from conservative defaults, otherwise marked unknown; the memory class decides what the estimate constrains; estimates are calibrated from measured peak memory and spill per unit composition ([CORE 4.2]({workspace}/documentation#3)), at a high percentile with a margin; and declared resources act as a floor. With nothing known, the declared or default request is used and the estimate is marked unknown, neither flagged nor refused.
- **Effective ceiling.** Amended by [D47](0047-control-plane-structure.md): the per-unit ceiling is the lower of the value a tenant Admin declares on the pool and the maximum its agents report ([D40](0040-protocol-between-the-control-and-data-planes.md)).

## Follow-ups

- Capacity as the selection step between engines at one location, applied when Spark or another such engine is added. The estimation method was set by [D47](0047-control-plane-structure.md); its expansion factors, percentile and margin are tuned from measurements.
