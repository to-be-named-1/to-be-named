# 25. Processing engines and runtimes

Date: 2026-10-11
Applies to: platform.controlPlane, platform.unitRuntime, warehouses

## Status

Accepted

Amended by [27. Ibis for relational node definitions](0027-ibis-for-relational-node-definitions.md)
Amended by [29. First development slice](0029-first-development-slice.md)
Amended by [32. Execution unit structure](0032-execution-unit-structure.md)
Amended by [34. Capacity and size](0034-capacity-and-size.md)
Amended by [44. Minimum technology stack](0044-minimum-technology-stack.md)

## Context

**Engine selection is by location, not size** (D25). Moving data costs more than computing where it sits. Size only affects the extraction cap and the capacity check; once an engine shares a location with the in-process engines, such as Spark, capacity chooses between them ([D34](0034-capacity-and-size.md)).

**One definition per built-in node** (D25, [D27](0027-ibis-for-relational-node-definitions.md)). A design with an in-process implementation plus optional SQL lowerings was rejected because it meant two implementations for some nodes. Built-in nodes are now Ibis expressions, with Polars implementations only by justified exception ([D27](0027-ibis-for-relational-node-definitions.md), amended).

**Snowflake as the single second warehouse for v1** (D25). One warehouse rather than two, because each adds a conformance column, a paid CI account and an adapter. Snowflake over BigQuery because it runs on all three major clouds (which matters for hybrid customers), offers longer time travel on enterprise editions (supporting replay under [D4](0004-datasets-as-first-class-objects.md)), and is what data-engineering buyers most often run. BigQuery was recognized as the technically easier adapter.

**Data moves only out of warehouses** (D25). When inputs sit in different locations, each warehouse's share is reduced by pushdown and the results are processed in-process. Staging the smaller side into the warehouse was dropped: it required write access the owner may not grant, could copy governed data (such as classified uploads) outside the platform's control, and created temporary tables to track. The cost (a small upload joined with a large warehouse table) is mitigated by pushdown before extraction and by the plan suggesting a warehouse storage target.

**No platform-run Spark in v1.** Spark as the only engine was rejected: it is slower on data that fits one machine, adds start-up latency to interactive use, makes the single-machine install heavier, nests a second scheduler inside units, and handles the Polars group poorly. Spark as an added engine was deferred: warehouse data is already covered by pushdown, genomics uses container fan-out, and lake-scale customers usually run their own Spark. Ibis's PySpark backend makes adding it later cheap.

**Repartition step instead of a distributed engine** (D25). Most dataframe work is local to a partition or a key; a repartition step supplies the shuffle that Spark would otherwise provide. Work that no key can divide remains flagged.

**Conformance matrix.** Engines disagree on integer division, nulls, casts, timestamps, rounding, float aggregation and collation. Because the planner, not the user, chooses where a node runs, the same node must give the same answer on every engine; the matrix enforces this.

As first recorded, the smaller input was staged into the warehouse, and Polars was the recommended default for Python.

The reasoning on a unit as a container with the runtime in the segment, in [D32](0032-execution-unit-structure.md), also cites this decision.

## Decision

The runtime is a property of the node type. Built-in relational nodes are defined once, as Ibis expressions ([D27](0027-ibis-for-relational-node-definitions.md)), and run on DuckDB inside an execution unit or are pushed down to a warehouse; other built-in tabular nodes are implemented in Polars and run in-process only; non-tabular families run in container runtimes and scale by fan-out. Placement follows where the data lives, not how large it is. Amended by [D27](0027-ibis-for-relational-node-definitions.md) and [D34](0034-capacity-and-size.md): built-in tabular nodes are Ibis first, with Polars by justified exception, and each unit's working set is checked against backend capacity.

- **Layers.** The **backend** (Kubernetes, HPC agent, cloud batch) decides where units run; the **runtime** (SQL, Polars, Python, container command) decides what runs inside a unit and is declared by the node type, including third-party node plugins ([D18](0018-format-types-plugin-implementations-and-bindings.md)); the **tools** are the libraries and binaries in the node's image. Only the runtime varies with the kind of data.
- **Built-ins.** Each built-in node has exactly one implementation. Nodes intended for pushdown — filter, select, join, aggregate, window, union, sort, deduplicate and pivot with fixed columns — are written in SQL. Nodes more naturally expressed as dataframe code — resample, fill, fuzzy matching, pivot over data-dependent values, sequential and stateful logic, parsing — are written in Polars and are never pushed down. Moving a node from one group to the other is a new node version. Amended by [D27](0027-ibis-for-relational-node-definitions.md): nodes intended for pushdown are defined as Ibis expressions rather than SQL text, and this group absorbs operations previously assigned to Polars wherever Ibis can express them. Amended again by [D27](0027-ibis-for-relational-node-definitions.md): Ibis on DuckDB is the engine for every built-in node, and a built-in node is implemented in Polars only by justified exception.
- **Dialects.** SQL nodes use the portable subset of SQL and are translated per dialect (for example with SQLGlot). A node that relies on dialect-specific constructs declares the dialects it supports. Under [D27](0027-ibis-for-relational-node-definitions.md) this compilation is performed by Ibis, which itself uses SQLGlot.
- **In-process.** DuckDB and Polars run together in one process inside a unit and exchange data as Arrow. Consecutive nodes on the same engine are chained into one **engine segment** — a single DuckDB query or Polars lazy plan — so each optimizer sees the whole segment; data changes hands only at segment boundaries. Heavy joins and aggregations fall to DuckDB, which spills to disk. Memory and thread limits for both engines are set from the unit's resource allocation, and DuckDB's spill directory is sized from it in the same way ([D34](0034-capacity-and-size.md)).
- **Selection.** Precedence: explicit override, then hard constraints (restricted data may not leave its warehouse; placement and residency; deferred from the first release, [D26](0026-placement-constraints.md)), then dialect capability, then data location. Relational nodes whose inputs share one warehouse are pushed down; inputs in files, object storage or uploads are processed in-process. At the first Polars node after warehouse data, the planner pushes down everything before it and extracts the reduced result.
- **Size.** Size does not select the engine. Extraction is capped by a configurable limit, and a plan that exceeds it asks the author instead of proceeding. An opt-in cost policy may prefer a cheaper placement, and a single-node guideline flags work beyond in-process capacity. Amended by [D34](0034-capacity-and-size.md): the single-node guideline becomes a capacity check in the plan; and once an engine is added that reads the same location as the in-process engines, such as Spark, the choice between engines at one location is made by capacity.
- **Data movement.** Data moves only out of warehouses into execution units, never into a warehouse. Where a node's inputs sit in different locations, each warehouse's share of the work is first reduced by pushdown and the reduced results are processed in-process. The planner writes to a warehouse only to publish a dataset whose storage target is that warehouse ([D4](0004-datasets-as-first-class-objects.md), [D15](0015-atomic-publication.md)). Where data held elsewhere forces a large extraction, the plan suggests giving that data the warehouse as its storage target, which makes the work eligible for pushdown; the planner never moves it on its own.
- **Repartition.** Where a node must group by a key other than the partitioning of its input, for example a fill-forward per customer over data partitioned by day, the planner inserts a repartition step: a unit that rewrites the data hash-bucketed by that key, after which the node fans out per bucket. The key is taken from the grouping the node declares. This provides the shuffle that a distributed engine would otherwise supply, without one. Work that cannot be divided by any key, such as a global sort or a join of two very large tables that cannot be bucketed to match, remains flagged by the capacity check ([D34](0034-capacity-and-size.md)).
- **Visibility.** The plan shows each unit's engine, location and the reason for the choice before the run starts. Users do not choose engines for built-in nodes.
- **Correctness.** Every Ibis and SQL node is conformance-tested against DuckDB and each supported warehouse dialect, since translation can change behavior around nulls, casts, timestamps and float aggregation. The engine family forms part of the cache key.
- **Warehouses.** The first release pushes down to Postgres and Snowflake. Further warehouses are added in later releases. Amended by [D29](0029-first-development-slice.md): the first development slice runs everything in-process on DuckDB and Polars; pushdown follows.
- **Code nodes.** SQL and Ibis (both eligible for pushdown, [D27](0027-ibis-for-relational-node-definitions.md)), Polars and pandas (in-process), and container commands for command-line tools such as samtools, BWA and GATK. All are supported on equal terms; none is designated the default.
- **Non-tabular.** Semi-structured data uses SQL where DuckDB handles it and Python otherwise (XML, HL7, FHIR). Text, images and ML artifacts run in Python runtimes, with GPUs where declared. Genomics runs as container commands, often on HPC agents. These scale by fan-out over items, partitions or splits ([CORE 6.18]({workspace}/documentation#3), [CORE 6.19]({workspace}/documentation#3)). Tabular data crosses unit boundaries as Arrow-readable files; other data crosses as artifact manifests. Amended by [D44](0044-minimum-technology-stack.md): managed tabular datasets on object storage are stored as Parquet.
- **Later.** Spark as a plugin executing against customer-operated clusters; Flink if streaming is added ([D6](0006-streaming.md), [D12](0012-streaming-readiness.md)), and Ray for distributed Python and ML workloads, likewise against customer-operated clusters ([D22](0022-deployment-topologies.md)).

## Follow-ups

- Spark, Flink and Ray against customer-operated clusters. Identification of the Polars exceptions through the [D27](0027-ibis-for-relational-node-definitions.md) spike, before the palette is designed.
