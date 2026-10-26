# 59. Column lineage

Date: 2026-10-26
Applies to: platform.webApp, platform.controlPlane, platform.database, platform.unitRuntime, platform.derivationUnit

## Status

Accepted

Amends [10. Where column-level lineage stops](0010-where-column-level-lineage-stops.md)
Amends [27. Ibis for relational node definitions](0027-ibis-for-relational-node-definitions.md)
Amends [57. Node-type contract](0057-node-type-contract.md)

## Context

[D10](0010-where-column-level-lineage-stops.md) derived column lineage for SQL and built-in declarative nodes and left custom code nodes at task level, with declared mappings offered only to custom code nodes. [D57](0057-node-type-contract.md) then tied derived lineage to plans. Both key lineage on something other than what it needs ([D58](0058-behavior-follows-properties.md)): a representation of the node's work that the platform can analyze. The compiled query of an Ibis or SQL plan is one; so is a Polars lazy plan, whether a plan node builds it or eager code returns it, and the platform's own eager node types had no way to declare lineage at all.

Any parameter may hold an expression ([D57](0057-node-type-contract.md)), so the columns a node acts on, and with them its lineage, may differ between runs even for a plan.

## Decision

Column lineage is derived from whatever the platform can analyze of the work a run executed, column by column, and is otherwise declared or task-level.

- **Sources.** Lineage is derived from the compiled query of an Ibis or SQL plan, and from a Polars lazy plan, built by a plan node or returned by eager code. Ibis and SQL plans are analyzed through the SQL they compile to, so one extractor serves both.
- **Per run.** Lineage is recorded for every node of every run, from what the run executed. Lineage shown before a run, from the cached derivation ([D57](0057-node-type-contract.md)), is a preview. Lineage that is the same between runs is stored once.
- **Per column.** Only the columns that pass through something the extractor cannot follow, such as a function applied to whole frames or an intermediate result the code materialized, become task-level; the other columns stay derived. A function applied to identified columns keeps them as its sources.
- **Direct only.** Derived lineage records direct dependencies, as [D10](0010-where-column-level-lineage-stops.md) set: the columns a filter's predicate or a join's keys read are not sources of the output. A column computed from rows rather than columns, such as a count, or taken from a constant, is labeled as such rather than as unknown.
- **Declarations.** Column mappings may be declared by any eager node type, by any code node and on any node of a workflow, whatever its type. A declaration fills only the columns that would otherwise be task-level. Derived lineage takes precedence, and a declaration on a node takes precedence over its type's. A declaration on a node changes nothing that runs and is part of no cache key.
- **Checked declarations.** The compiler checks that every column a declaration names exists in the node's input and output schemas, and a run checks those of a dynamic output once it is known. A declaration that names a missing column is reported as a note and left out of the run's lineage.
- **Labels.** Each column is shown as derived, declared or task-level ([D10](0010-where-column-level-lineage-stops.md)); a declared column also shows where it was declared, on the node type or on the node.
- **Extractors.** An extractor is pinned, with the library whose representation it reads, to the image that runs it, and is tested against a corpus. An extractor that fails, or has no support for a library's version, yields task-level lineage: lineage is never wrong and never stops a run.
- **Amends.** [D10](0010-where-column-level-lineage-stops.md): lineage is derived from any representation that can be analyzed, recorded per run and per column, and declarations are open to every node, on its type, in its code or on the node itself. [D27](0027-ibis-for-relational-node-definitions.md): lineage of Ibis nodes is derived from their compiled SQL. [D57](0057-node-type-contract.md): column lineage is not a capability of plans alone.

## Consequences

- Lineage of eager Polars code depends on the eager interface handing inputs over as lazy frames and accepting a lazy frame back (design agenda).
- The Polars extractor reads Polars internals, so its adapter follows the Polars version of each image.
- Lineage grows with runs; storing identical lineage once keeps it small.

## Rejected alternatives

- Lineage derived for plans only. Eager code that returns a Polars lazy plan can be analyzed as well.
- Lineage derived once, when a workflow is compiled. Values computed per run change which columns a node reads.
- Declarations only for custom code nodes. The platform's own eager node types could not declare lineage, and authors could not declare it for nodes of a type someone else published.
- Declarations that replace derived lineage. Derived lineage is checked against what ran; a declaration that replaced it could hide what a node does.
- Lineage matched by column name where nothing can be analyzed. It is often right but sometimes wrong, and classification and erasure follow lineage ([DE 5.9]({workspace}/documentation#4)).
- Walking the Ibis expression tree. It needs a walker per operation, while the compiled SQL serves Ibis and SQL nodes with one extractor.

## Follow-ups

- Whether the partitioning and ordering columns of a window are direct sources of its output.
- The form of declared mappings: in node types and code files with the interfaces code files follow, and on nodes with the workflow documents (design agenda).
- Coverage of the Polars extractor: selection by pattern or type, colliding join suffixes, and exploded or unnested columns.
