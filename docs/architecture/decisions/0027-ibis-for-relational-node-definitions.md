# 27. Ibis for relational node definitions

Date: 2026-10-11
Applies to: platform.unitRuntime

## Status

Partial

Amends [25. Processing engines and runtimes](0025-processing-engines-and-runtimes.md)
Amended by [47. Control-plane structure](0047-control-plane-structure.md)
Amended by [57. Node-type contract](0057-node-type-contract.md)
Amended by [59. Column lineage](0059-column-lineage.md)

## Context

**Ibis adopted, DuckDB kept** (D27). Ibis is a dataframe API that compiles to engines, not an engine. Replacing DuckDB with Ibis's Polars backend was rejected because it loses DuckDB's spilling of large joins and aggregations to disk. Ibis moves operations such as fill-forward and pivots from "Polars, never pushed down" to "pushable", and gives Python authors a pushdown-capable code node in v1.

**Ibis first for every built-in node** (D27, amended). One engine for the palette means one memory manager, one spilling model, one in-process conformance column and default eligibility for pushdown. Builtin and vectorized UDFs let fuzzy matching and parsing stay in Ibis. Using Ibis's Polars backend instead was rejected: Polars does not document spilling of operator state, and its semantics are further from the SQL warehouses that conformance compares against.

The reasoning on one definition per built-in node, in [D25](0025-processing-engines-and-runtimes.md), and on Go for the control plane and the agent, in [D44](0044-minimum-technology-stack.md), also cites this decision.

## Decision

Built-in relational nodes are defined as **Ibis** expressions rather than as hand-written portable SQL. Ibis compiles each expression into the dialect of the engine that runs it: DuckDB inside an execution unit, or the warehouse when the node is pushed down. Ibis is an API above the engines, not an engine; DuckDB remains the in-process engine. The same API is offered from the first release as a code node for Python authors whose transformations should be eligible for pushdown, which [D25](0025-processing-engines-and-runtimes.md) had deferred.

- **Amends.** [D25](0025-processing-engines-and-runtimes.md). The split between built-in nodes becomes Ibis, eligible for pushdown, and Polars, in-process only. The SQL group of [D25](0025-processing-engines-and-runtimes.md) is replaced by the Ibis group.
- **Ibis group.** Every built-in node that can be expressed as an Ibis expression. This includes operations previously assigned to Polars because they are awkward in portable SQL, such as fill-forward and fill-backward through window functions, pivots and date arithmetic, so less data needs to be extracted from a warehouse. The final assignment of each node is made when the built-in palette is designed.
- **Ibis first.** Ibis on DuckDB is the engine for every built-in node, and Polars is an exception rather than half of the palette. A built-in node is implemented by the first of four tiers that can express it: a portable Ibis expression, eligible for pushdown to every supported dialect; an Ibis expression calling a native backend function through a builtin UDF, such as DuckDB's string-similarity functions, eligible for pushdown only to dialects that declare an equivalent; an Ibis expression with a vectorized PyArrow UDF, in-process only but still inside the DuckDB segment, so that the surrounding joins and aggregations keep spilling to disk; and, by justified exception, a Polars implementation. Fuzzy matching and complex parsing therefore move to the Ibis tiers.
- **Polars group.** Reduced to justified exceptions, chiefly logic in which each row depends on the result computed for the previous row, which window functions cannot express and Ibis does not support through recursive queries. Code nodes are unchanged: Ibis, Polars and pandas are all supported.
- **Order and spilling.** Since SQL engines have no row order, every node whose result depends on order declares a sort key. DuckDB does not spill `PIVOT`, `list()`, `string_agg()` or ordered aggregates to disk; nodes using them have the non-spilling memory class ([D34](0034-capacity-and-size.md)), which is derived from their compiled expression ([D57](0057-node-type-contract.md)).
- **One definition.** The Ibis expression is the single definition of a node; compiled SQL is derived from it. Engine segments are preserved, since a chain of Ibis nodes compiles to a single query.
- **Conformance.** The conformance matrix is retained ([CORE 1.12]({workspace}/documentation#3)). Where Ibis does not support an operation on a backend, the node declares that dialect unsupported and is not pushed down to it.
- **Versioning.** An Ibis upgrade can change compiled SQL, so the Ibis version forms part of the node version and is pinned in the node's image.
- **Lineage.** Column-level lineage of these nodes is derived from their compiled SQL ([D10](0010-where-column-level-lineage-stops.md), [D59](0059-column-lineage.md)).
- **Compilation.** Ibis compiles in the data plane, in Python, in the derivation units that hand compiled plans to execution units ([D57](0057-node-type-contract.md)). The planner needs only to know whether a node is eligible for pushdown and which dialects it supports, so the choice of control-plane language is not constrained; Go was chosen ([D44](0044-minimum-technology-stack.md)).
- **Condition.** Confirmed subject to a spike, which classifies each candidate built-in node into one of the four Ibis-first tiers, producing the list of Polars exceptions; runs the nodes on DuckDB, including joins, aggregations, sorts and windows larger than memory under a fixed memory limit; checks that the nodes compile for Postgres and Snowflake, with execution against those warehouses following pushdown ([D29](0029-first-development-slice.md)); and reviews the maintenance and release practices of the Ibis project, which becomes a core dependency. Coverage gaps are reported before the palette is designed.
- **Spilling forms.** Added to the spike by [D47](0047-control-plane-structure.md): whether Ibis compiles fixed-column pivots and ordered aggregates on DuckDB into forms that spill. DuckDB implements every `PIVOT` through `list()`, which does not spill; where Ibis does not produce a spilling form, the palette implements such nodes as filtered aggregates or equivalents that do not sort, and only pivots over values discovered at run time keep the non-spilling memory class.
- **Deferred.** Checking that the palette also compiles on Ibis's PySpark backend is deferred until a Spark engine is taken up ([D25](0025-processing-engines-and-runtimes.md)).

## Rejected alternatives

- Replacing DuckDB with Ibis's Polars backend for local execution. DuckDB documents out-of-core grouping, joining, sorting and windowing, while Polars' streaming engine processes data in batches without documented spilling of operator state; Ibis on DuckDB compiles to SQL, the same path used for Postgres and Snowflake, which eases conformance; and DuckDB is Ibis's default and most complete backend. The objection that Polars is present in any case no longer applies once built-in nodes are Ibis first.

## Follow-ups

- **Spike (condition for full confirmation):** classify each candidate built-in node into the four Ibis-first tiers and so derive the Polars exceptions; run the nodes on DuckDB, including operations larger than memory under a fixed memory limit; check that they compile for Postgres and Snowflake; and review the Ibis project's maintenance and release practices; and, added by [D47](0047-control-plane-structure.md), whether fixed-column pivots and ordered aggregates compile on DuckDB into forms that spill.
- PySpark compile check, deferred until a Spark engine is taken up.
