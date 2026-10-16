# 32. Execution unit structure

Date: 2026-10-11
Applies to: platform.controlPlane, platform.unitRuntime, platform.commandUnit

## Status

Accepted

Amends [25. Processing engines and runtimes](0025-processing-engines-and-runtimes.md)
Amended by [50. Development mode](0050-development-mode.md)

## Context

**A unit is a container; the runtime belongs to the segment** (D32). [D25](0025-processing-engines-and-runtimes.md) and its worked examples already placed several engines in one unit, which contradicted "one runtime, one process". Making the segment explicit resolves this and lets warehouse queries join later as one more segment kind.

## Decision

An execution unit is one container running one image, with one resource request and one attempt lifecycle, reading its inputs from storage and writing its outputs to storage. Inside it, nodes are grouped into **engine segments** — consecutive nodes on one engine — which hand data to each other in memory as Arrow. Work is therefore described at three levels: the node (what the user draws), the segment (what one engine executes) and the unit (what the orchestrator dispatches).

- **Amends.** The [vocabulary]({workspace}/documentation#2) and [D25](0025-processing-engines-and-runtimes.md): a unit was described as "one image, one process" whose nodes share a runtime, while [D25](0025-processing-engines-and-runtimes.md) and its worked examples placed several engines in one unit. The runtime is now a property of the segment, and the fusion condition "share a runtime" becomes "share an image and execution location".
- **Segment kinds.** A DuckDB query compiled from Ibis, including any vectorized PyArrow UDFs it calls ([D27](0027-ibis-for-relational-node-definitions.md)); a Polars lazy plan; or a Python block. A warehouse query is added as a further kind when pushdown is introduced.
- **Binding.** Ibis nodes are defined on unbound tables, carrying a schema and a name but no data or connection. The unit runtime binds them at execution time, registering the unit's inputs on an in-process DuckDB connection, or, once pushdown exists, on a warehouse connection. Whether a node is pushed down is therefore decided by the planner at binding, not by how the node is written ([D25](0025-processing-engines-and-runtimes.md)).
- **Container commands.** A node that runs a command-line tool is always a unit of its own, since the tool is the process.
- **Code nodes.** A Python code node runs in the image built from its declared dependencies (CORE 1.10). It may share a unit with built-in nodes only when that image is built on the platform's base image, as platform builds are by default.
- **Pushdown.** When introduced, the unit's runtime submits the warehouse query and streams its result into the next segment. A fully pushed-down unit is a unit with a single warehouse segment. The model does not change.
- **Sessions.** Amended by [D50](0050-development-mode.md): a unit runs in its own container or in a session container that runs successive units, each in a fresh process, so the plan and its unit boundaries are unchanged.

## Follow-ups

- Units spanning several containers scheduled together, for training across machines (MLE 2.1), or Ray against customer-operated clusters ([D25](0025-processing-engines-and-runtimes.md)).
