# 29. First development slice

Date: 2026-10-11
Applies to: platform.agent, platform.controlPlane

## Status

Accepted

Amends [17. Dataset families and first-release scope](0017-dataset-families-and-first-release-scope.md)
Amends [22. Deployment topologies](0022-deployment-topologies.md)
Amends [25. Processing engines and runtimes](0025-processing-engines-and-runtimes.md)

## Context

**A pull-based agent in every deployment** (D29). Having the control plane call the Docker or Kubernetes API directly in self-hosted installations was rejected: hybrid would then need a second execution path. With the agent everywhere, hybrid differs only in where the control plane runs. The cost is one extra component and one extra hop on a single machine.

## Decision

Development begins with a deliberately narrow slice of the catalog: the tabular family, the single-machine container deployment and Kubernetes, in-process execution on DuckDB through Ibis with Polars by exception, the visual canvas and round-tripping to text in git.

- **Data.** The tabular family only ([D17](0017-dataset-families-and-first-release-scope.md)). File groups, linked items, sharded collections and splittability (CORE 6.16 – 6.19) are therefore not required in the first slice. The other five families follow through the same family interface.
- **Backends.** The single-machine container deployment (CORE 2.17) and Kubernetes. HPC agents and cloud batch follow.
- **External readability.** Iceberg metadata is projected for managed datasets on object storage, so external engines can read them as tables ([D42](0042-catalog-persistence.md)); projection is on by default wherever a catalog is configured ([D44](0044-minimum-technology-stack.md)).
- **Engines.** In-process only ([D25](0025-processing-engines-and-runtimes.md)): Ibis on DuckDB for every built-in node, with Polars by justified exception and for code nodes ([D27](0027-ibis-for-relational-node-definitions.md)). Built-in nodes are defined as Ibis expressions so that they need no rewriting when pushdown is introduced. Warehouse pushdown, the warehouse connection policy ([D28](0028-warehouse-connection-policy-and-plan-pinning.md)), Spark and Flink follow.
- **Authoring.** The canvas (CORE 1.1) and round-tripping to text in git (CORE 1.6) are both in the first slice, so the canonical text syntax is settled together with the IR specification.
- **Agent.** The data plane is driven by a pull-based execution agent in every deployment, including single-machine and self-hosted ones; the control plane never calls a backend's API directly. Hybrid deployment then differs only in where the control plane runs, not in how work is executed ([D22](0022-deployment-topologies.md)).
- **License.** The repository is private. The license is chosen before it is made public or accepts external contributions, in line with [D5](0005-distribution-and-tenancy.md).
- **Stack.** The languages, interfaces and libraries the first slice is built with are recorded in [D44](0044-minimum-technology-stack.md).

## Follow-ups

- After the first slice: the other five dataset families, HPC agents and cloud batch, warehouse pushdown with connection policy, and the remaining deployment topologies. License before the repository is made public.
